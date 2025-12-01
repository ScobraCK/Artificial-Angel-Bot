from enum import Enum
from functools import partial
from io import StringIO
from itertools import batched

from discord import ui, ButtonStyle, SeparatorSpacing
from html2text import HTML2Text

from aabot.crud.character import get_character
from aabot.pagination.equipment import get_uw, equipment_detail_ui
from aabot.pagination.index import arcana_basic_text
from aabot.pagination.skills import get_skill_name, get_skill_text
from aabot.pagination.view import create_content_button, to_content, BaseContainer, BaseView, ContentMap
from aabot.utils import api
from aabot.utils.assets import CHARACTER_THUMBNAIL, SKILL_THUMBNAIL
from aabot.utils.emoji import to_emoji
from aabot.utils.error import BotError
from aabot.utils.utils import base_param_text, battle_param_text, calculate_base_stat, character_title, possessive_form
from common import enums, schemas, timezones
from common.database import SessionAA

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

class CharacterOptions(Enum):
    INFO = 'Basic Information'
    PROFILE = 'Profile'
    SKILL = 'Skills'
    UW = 'Unique Weapon'
    ARCANA = 'Arcana'
    VOICELINES = 'Voicelines'
    MEMORIES = 'Memories'
    LAMENT = 'Lament'
    STATS = 'Stats'

class CharacterContainer(BaseContainer):
    def add_release_warning(self):
        self.add_item(
            ui.TextDisplay('>>> **WARNING: This character has not yet been released as a playable character. Some information may not be available and all details are subject to change.**')
        ).add_item(ui.Separator(visible=False))
        return self

    async def add_alt_section(self, char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings):
        if (alt_chars := await fetch_alt_chars(char_id)) and len(alt_chars) > 1:
            self.add_item(ui.Separator(spacing=SeparatorSpacing.large))
            self.add_item(
                ui.Section(
                    ui.TextDisplay('Alternate versions exist for this character'),
                    accessory=create_content_button(await switch_char_ui(alt_chars, language, cs), 'Switch', save_state=True)
                )
            )
        return self


async def fetch_alt_chars(char_id: int) -> list[int]:
    resp = await api.fetch_api(
        api.CHARACTER_ALTS_ID_PATH.format(char_id=char_id),
        response_model=dict[int, list[int]]
    )
    return next(iter(resp.data.values()))

async def get_release_status(char_id: int) -> bool:
    resp = await api.fetch_api(
        api.CHARACTER_INFO_PATH.format(char_id=char_id),
        response_model=schemas.Character
    )
    return timezones.check_active(resp.data.start, timezones.END_TIME, enums.Server.Japan)

async def get_base_stats(level: str, rarity: enums.CharacterRarity, character: schemas.Character|int, potential: schemas.CharacterPotential|None = None) -> schemas.BaseParameters:
    if isinstance(character, int):
        character = (await api.fetch_api(
            api.CHARACTER_INFO_PATH.format(char_id=character),
            response_model=schemas.Character
        )).data
    if not potential:
        potential = (await api.fetch_api(
            api.CHARACTER_POTENTIAL_PATH,
            response_model=schemas.CharacterPotential
        )).data
        
    total_stats = potential.levels.get(level)
    if not total_stats:
        raise BotError(f'No data for level {level}.')
    base_rarity = character.rarity
    coeffs = potential.coefficients[base_rarity][rarity]

    return schemas.BaseParameters(
        str=calculate_base_stat(total_stats, coeffs.m, coeffs.b, character.base_coefficients.str, character.gross_coefficient),
        dex=calculate_base_stat(total_stats, coeffs.m, coeffs.b, character.base_coefficients.dex, character.gross_coefficient),
        mag=calculate_base_stat(total_stats, coeffs.m, coeffs.b, character.base_coefficients.mag, character.gross_coefficient),
        sta=calculate_base_stat(total_stats, coeffs.m, coeffs.b, character.base_coefficients.sta, character.gross_coefficient)
    )

async def switch_char_ui(chars: list[int], language: enums.LanguageOptions, cs: schemas.CommonStrings) -> BaseContainer:
    container = BaseContainer()
    async with SessionAA() as session:
        for char_id in chars:
            name = await api.fetch_name(char_id, language)
            char_info = await get_character(session, char_id)
            element_emoji = await to_emoji(session, enums.Element(char_info.element))
            job_emoji = await to_emoji(session, enums.Job(char_info.job))
            container.add_item(
                ui.Section(
                    ui.TextDisplay(f'**{character_title(name.title, name.name)}**'),
                    ui.TextDisplay(
                        f'**Id:** {char_id}\n'
                        f'**Element:** {element_emoji}{cs.element[char_info.element]}\n'
                        f'**Base Rarity:** {char_info.base_rarity}\n'
                        f'**Class:** {job_emoji}{cs.job[char_info.job]}\n'
                    ),
                    accessory=ui.Thumbnail(CHARACTER_THUMBNAIL.format(char_id=char_id, qlipha=False)),
                ),
            ).add_item(
                ui.ActionRow(
                    create_content_button(
                        await character_option_map(char_id),
                        'Select',
                        load_state=True
                    )
                )
            )
            if char_id != chars[-1]:
                container.add_item(ui.Separator())

    return container

async def character_option_map(char_id: int) -> ContentMap:
    released = await get_release_status(char_id)
    content = {
        CharacterOptions.INFO.value: partial(character_info_ui, char_id, released=released),
        CharacterOptions.PROFILE.value: partial(character_profile_ui, char_id, released=released),
        CharacterOptions.SKILL.value: partial(character_skill_ui, char_id, released=released),
        CharacterOptions.UW.value: partial(character_uw_ui, char_id, released=released),
        CharacterOptions.ARCANA.value: partial(character_arcana_ui, char_id, released=released),
        CharacterOptions.VOICELINES.value: partial(character_voiceline_ui, char_id, released=released),
        CharacterOptions.MEMORIES.value: partial(character_memory_ui, char_id, released=released),
        CharacterOptions.LAMENT.value: partial(character_lament_ui, char_id, released=released),
        CharacterOptions.STATS.value: partial(character_stats_ui, char_id, released=released),
    }

    return to_content(content)

async def character_info_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> BaseContainer:
    container = CharacterContainer()
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        container.add_release_warning()
    
    char_resp = await api.fetch_api(
        api.CHARACTER_INFO_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Character
    )
    char_data = char_resp.data
    skills_resp = await api.fetch_api(
        api.CHARACTER_SKILL_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Skills
    )
    skills_data = skills_resp.data

    async with SessionAA() as session:
        element_emoji = await to_emoji(session, char_data.element)
        job_emoji = await to_emoji(session, char_data.job)
        str_emoji = await to_emoji(session, 'str')
        dex_emoji = await to_emoji(session, 'dex')
        mag_emoji = await to_emoji(session, 'mag')
        sta_emoji = await to_emoji(session, 'sta')

    # Basic info
    container.add_item(
        ui.Section(
            ui.TextDisplay(f'### {character_title(char_data.title, char_data.name)}'),
            ui.TextDisplay(
                (
                    f'**Id:** {char_data.char_id}\n'
                    f'**Element:** {element_emoji}{cs.element[char_data.element]}\n'
                    f'**Base Rarity:** {enums.CharacterRarity(char_data.rarity).name}\n'
                    f'**Class:** {job_emoji}{cs.job[char_data.job]}\n'
                    f'**Base Speed:** {char_data.speed}\n'
                    f'**UW:** {char_data.uw}\n'
                )
            ),
            accessory=ui.Thumbnail(CHARACTER_THUMBNAIL.format(char_id=char_data.char_id, qlipha=False))
        )
    )
    
    # Base stats
    if (base_rarity := char_data.rarity) == enums.CharacterBaseRarity.N:
        rarity = enums.CharacterRarity.N
        level = '100.0'
    elif base_rarity == enums.CharacterBaseRarity.R:
        rarity = enums.CharacterRarity.SSRPlus
        level = '160.0'
    else:
        rarity = enums.CharacterRarity.LR
        level = '240.0'
    base_stats = await get_base_stats(level, rarity, char_data)
    container.add_item(
        ui.TextDisplay(
            f'**Stats** (Lv {level.removesuffix('.0')})\n'
            f'{str_emoji} {base_stats.str:,} '
            f'{dex_emoji} {base_stats.dex:,}\n'
            f'{mag_emoji} {base_stats.mag:,} '
            f'{sta_emoji} {base_stats.sta:,}\n'
        )
    ).add_item(ui.Separator(visible=False))

    # Skills
    if skills_data:
        skill_text = StringIO()
        skill_text.write('**__Active Skills__**\n')
        for skill in skills_data.actives:
            skill_text.write(f'{skill.name} | **CD:** {skill.max_cooltime}\n')
        container.add_item(ui.TextDisplay(skill_text.getvalue()))

        if skills_data.passives:
            skill_text = StringIO()
            skill_text.write('**__Passive Skills__**\n')
            for skill in skills_data.passives:
                if skill.name and skill.name != '*':
                    skill_text.write(f'{skill.name}\n')
            container.add_item(ui.TextDisplay(skill_text.getvalue()))
    else:
        container.add_item(ui.TextDisplay('*Skill data currently unavailable*'))

    await container.add_alt_section(char_id, language, cs)
    container.add_version(char_resp.version)
    
    return container

async def character_profile_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> BaseContainer:
    container = CharacterContainer()
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        container.add_item(ui.TextDisplay('Profile data is unavailable for unreleased characters.'))
        return container

    profile_resp = await api.fetch_api(
        api.CHARACTER_PROFILE_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Profile
    )
    profile_data = profile_resp.data
    name = await api.fetch_name(char_id, language)

    container.add_item(
        ui.Section(
            ui.TextDisplay(f'### {character_title(name.title, name.name)}'),
            ui.TextDisplay(
                (
                    f'**Id:** {profile_data.char_id}\n'
                    f'**Birthday:** {profile_data.birthday//100}/{profile_data.birthday%100}\n'
                    f'**Blood Type:** {profile_data.blood_type.name}\n'
                    f'**Height:** {profile_data.height}cm\n'
                    f'**Weight:** {profile_data.weight}kg\n\n'
                    f'**Song by:** {profile_data.vocalJP}\n'
                    # f'**Vocal (US):** {profile_data.vocalUS}\n'
                    f'**CV (JP):** {profile_data.voiceJP}\n'
                    f'**CV (US):** {profile_data.voiceUS}\n'
                )
            ),
            accessory=ui.Thumbnail(CHARACTER_THUMBNAIL.format(char_id=profile_data.char_id, qlipha=False))
        )
    ).add_item(
        ui.Separator()
    ).add_item(ui.TextDisplay(profile_data.description))

    await container.add_alt_section(char_id, language, cs)
    container.add_version(profile_resp.version)

    return container

async def character_skill_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> BaseContainer|list[ui.Container]:
    container = CharacterContainer()
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        container.add_release_warning()
    
    skill_resp = await api.fetch_api(
        api.CHARACTER_SKILL_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Skills
    )
    skill_data = skill_resp.data
    char_resp = await api.fetch_api(
        api.CHARACTER_INFO_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Character
    )
    char_data = char_resp.data

    async with SessionAA() as session:
        container.add_item(ui.TextDisplay(f'## {possessive_form(character_title(char_data.title, char_data.name))} Skills'))
        container.add_item(ui.TextDisplay('### __Active Skills__'))
        for skill in skill_data.actives:
            name = await get_skill_name(skill, char_data.uw)
            description = await get_skill_text(skill, skill_data.uw_descriptions, session)
            container.add_item(
                ui.Section(
                    ui.TextDisplay(f'### {name}'),
                    ui.TextDisplay(description),
                    accessory=ui.Thumbnail(SKILL_THUMBNAIL.format(skill_id=skill.id))
                )
            )
        
        temp_container = ui.Container()
        for skill in skill_data.passives:
            name = await get_skill_name(skill, char_data.uw)
            description = await get_skill_text(skill, skill_data.uw_descriptions, session)
            if name is None:
                continue
            if name == char_data.uw:
                temp_container.add_item(ui.TextDisplay(f'### {name}'))
                temp_container.add_item(ui.TextDisplay(description))
            else:
                temp_container.add_item(
                    ui.Section(
                        ui.TextDisplay(f'### {name}'),
                        ui.TextDisplay(description),
                        accessory=ui.Thumbnail(SKILL_THUMBNAIL.format(skill_id=skill.id))
                    )
                )

    if temp_container.content_length() > 0:  # Has passive skills
        if container.content_length() + temp_container.content_length() > 3900:  # Split into two containers
            passive_container = CharacterContainer()
            if not released:
                passive_container.add_release_warning()
            passive_container.add_item(ui.TextDisplay(f'### {possessive_form(character_title(char_data.title, char_data.name))} Skills'))
            passive_container.add_item(ui.TextDisplay('### __Passive Skills__'))
            for item in temp_container.children:
                passive_container.add_item(item)
            
            await container.add_alt_section(char_id, language, cs)
            container.add_version(skill_resp.version)
            await passive_container.add_alt_section(char_id, language, cs)
            passive_container.add_version(skill_resp.version)

            return [container, passive_container]
        else:  # Single Container
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay('### __Passive Skills__'))
            for item in temp_container.children:
                container.add_item(item)

    await container.add_alt_section(char_id, language, cs)
    container.add_version(skill_resp.version)

    return container

async def character_voiceline_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> list[ui.Container]:
    containers = []
    h = HTML2Text()
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        return BaseContainer('Voiceline data is unavailable for unreleased characters.')

    voiceline_resp = await api.fetch_api(
        api.CHARACTER_VOICE_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.CharacterVoicelines
    )
    voice_data = voiceline_resp.data
    profile_resp = await api.fetch_api(
        api.CHARACTER_PROFILE_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Profile
    )
    profile_data = profile_resp.data
    name = await api.fetch_name(char_id, language)

    batches = list(batched((voiceline for voiceline in voice_data.voicelines if voiceline.subtitle), 10))
    for i, batch in enumerate(batches):
        container = CharacterContainer()
        container.add_item(ui.TextDisplay(f'### {possessive_form(character_title(name.title, name.name))} Voicelines'))
        for voiceline in batch:
            container.add_item(ui.TextDisplay(f'**{voiceline.button_text}**\n{h.handle(voiceline.subtitle)}'))
        if i == len(batches) - 1 and profile_data.gacha_message:
            container.add_item(ui.TextDisplay(f'**Gacha Message 1**\n{h.handle(profile_data.gacha_message)}'))

        await container.add_alt_section(char_id, language, cs)
        container.add_version(voiceline_resp.version)
        containers.append(container)

    return containers

async def character_memory_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> list[ui.Container]:
    containers = []
    h = HTML2Text()
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        return BaseContainer('Memory data is unavailable for unreleased characters.')

    memory_resp = await api.fetch_api(
        api.CHARACTER_MEMORY_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.CharacterMemories
    )
    memory_data = memory_resp.data
    name = await api.fetch_name(char_id, language)
    for memory in memory_data.memories:
        container = CharacterContainer()
        container.add_item(ui.TextDisplay(f'### {possessive_form(character_title(name.title, name.name))} Memories'))
        container.add_item(ui.TextDisplay(f'**{memory.title}**\n{h.handle(memory.text)}'))

        await container.add_alt_section(char_id, language, cs)
        container.add_version(memory_resp.version)
        containers.append(container)
    return containers

async def character_uw_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> BaseContainer:
    container = CharacterContainer()

    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        return BaseContainer('Unique Weapon data is unavailable for unreleased characters.')

    uw_resp = await get_uw(char_id, language)
    if uw_resp is None:
        return BaseContainer('This character does not have a Unique Weapon.')
    uw_container = await equipment_detail_ui(uw_resp.data, cs)
    for item in uw_container.children:  # For add_alt_section function
        container.add_item(item)
    await container.add_alt_section(char_id, language, cs)
    container.add_version(uw_resp.version)
    return container

async def character_arcana_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> BaseContainer:
    container = CharacterContainer()

    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        return BaseContainer('Arcana data is unavailable for unreleased characters.')

    arcana_resp = await api.fetch_api(
        api.CHARACTER_ARCANA_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=list[schemas.Arcana]
    )
    arcana_data = arcana_resp.data
    name = await api.fetch_name(char_id, language)

    container.add_item(ui.TextDisplay(f'### {possessive_form(character_title(name.title, name.name))} Arcana'))
    for arcana in arcana_data:
        arcana_text = await arcana_basic_text(arcana, cs, language)
        container.add_item(ui.TextDisplay(arcana_text))

    await container.add_alt_section(char_id, language, cs)
    container.add_version(arcana_resp.version)

    return container

async def character_lament_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, show_jp: bool = True, released: bool|None = None) -> BaseContainer:
    h = HTML2Text()
    LYRIC_TEXT_ID = 1
    TOGGLE_BUTTON_ID = 2
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        return BaseContainer('Lament data is unavailable for unreleased characters.')

    container = CharacterContainer()

    lament_resp = await api.fetch_api(
        api.CHARACTER_LAMENT_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Lament
    )
    lament_data = lament_resp.data
    name = await api.fetch_name(char_id, language)

    if lament_data.youtubeJP and lament_data.youtubeUS:
        youtube_str = f'YouTube: [JP]({lament_data.youtubeJP}) | [EN]({lament_data.youtubeUS})'
    elif lament_data.youtubeJP:
        youtube_str = f'YouTube: [JP]({lament_data.youtubeJP})'
    elif lament_data.youtubeUS:
        youtube_str = f'YouTube: [EN]({lament_data.youtubeUS})'
    else:
        youtube_str = 'YouTube: N/A'

    jp_lyrics = h.handle(lament_data.lyricsJP)
    en_lyrics = h.handle(lament_data.lyricsUS)

    container.add_item(
        ui.Section(
            ui.TextDisplay(f'### {possessive_form(character_title(name.title, name.name))} Lament'),
            ui.TextDisplay(youtube_str),
            accessory=ui.Thumbnail(CHARACTER_THUMBNAIL.format(char_id=char_id, qlipha=False))
        )
    ).add_item(ui.TextDisplay(jp_lyrics if show_jp else en_lyrics, id=LYRIC_TEXT_ID))
    
    # Add toggle button
    container.extra['show_jp'] = show_jp
    container.extra['JP'] = jp_lyrics
    container.extra['EN'] = en_lyrics

    button = ui.Button(
        style=ButtonStyle.primary,
        label='Toggle Lyrics',
        emoji='🇯🇵' if show_jp else '🇺🇸',
        id=TOGGLE_BUTTON_ID
    )
    async def callback(interaction):
        view: BaseView = button.view
        current = view.extra.get('show_jp', True)
        if current:
            lyrics = view.extra['EN']  # swaps to opposite
        else:
            lyrics = view.extra['JP']
        view.extra['show_jp'] = not current
        view.find_item(LYRIC_TEXT_ID).content = lyrics
        view.find_item(TOGGLE_BUTTON_ID).emoji = '🇺🇸' if current else '🇯🇵'
        await view.update_view(interaction)
    button.callback = callback

    container.add_item(ui.ActionRow(button))
        
    await container.add_alt_section(char_id, language, cs)
    container.add_version(lament_resp.version)

    return container

async def character_stats_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings, released: bool|None = None) -> BaseContainer:
    container = CharacterContainer()
    # Released check
    if released is None:
        released = await get_release_status(char_id)
    if not released:
        container.add_release_warning()

    char_resp = await api.fetch_api(
        api.CHARACTER_INFO_PATH.format(char_id=char_id),
        query_params={'language': language},
        response_model=schemas.Character
    )
    char_data = char_resp.data

    container.add_item(
        ui.Section(
            ui.TextDisplay(f'### {possessive_form(character_title(char_data.title, char_data.name))} Stats'),
            ui.TextDisplay(f'**Base Parameter Coefficients** (Total: {char_data.gross_coefficient})\n{base_param_text(char_data.base_coefficients, cs)}'),
            accessory=ui.Thumbnail(CHARACTER_THUMBNAIL.format(char_id=char_data.char_id, qlipha=False))
        )
    ).add_item(
        ui.TextDisplay(f'**Battle Parameters**\n{battle_param_text(char_data.init_battle_paramters, cs)}')
    ).add_item(
        ui.TextDisplay('*Stats shown are initial stats applied to the character. Use `/calcstat` for ingame stat calculations.')
    )

    await container.add_alt_section(char_id, language, cs)
    container.add_version(char_resp.version)
    return container