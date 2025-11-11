from functools import partial
from io import StringIO
from itertools import batched

from discord import ui, Color, Interaction, SeparatorSpacing
from html2text import HTML2Text

from aabot.crud.character import get_character
from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.view import to_content, create_content_button, BaseView
from aabot.pagination.views import ButtonView
from aabot.utils import api
from aabot.utils.assets import RAW_ASSET_BASE, CHARACTER_THUMBNAIL, MOONHEART_ASSET_MEMORY
from aabot.utils.emoji import to_emoji
from aabot.utils.error import BotError
from aabot.utils.utils import character_title, possessive_form
from common import enums, schemas
from common.database import SessionAA

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

async def fetch_alt_chars():
    return [48, 117]

async def switch_char_ui(chars: list[int], language: enums.LanguageOptions, cs: schemas.CommonStrings) -> ui.Container:
    container = ui.Container()
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
                        partial(character_info_ui, char_id),
                        'Select',
                        load_state=True
                    )
                )
            )
            if char_id != chars[-1]:
                container.add_item(ui.Separator())

    return container

async def character_info_ui(char_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings) -> ui.Container:
    char_resp = await api.fetch_api(
        api.CHARACTER_PATH,
        path_params={'char_id': char_id},
        query_params={'language': language},
        response_model=schemas.Character
    )
    char_data = char_resp.data
    try:
        skills_resp = await api.fetch_api(
            api.CHARACTER_SKILL_PATH,
            path_params={'char_id': char_id},
            query_params={'language': language},
            response_model=schemas.Skills
        )
        skills_data = skills_resp.data
    except BotError:
        skills_data = None

    async with SessionAA() as session:
        element_emoji = await to_emoji(session, char_data.element)
        job_emoji = await to_emoji(session, char_data.job)

    container = ui.Container()
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

    # Alt button
    if (alt_chars := await fetch_alt_chars()):
        container.add_item(ui.Separator(spacing=SeparatorSpacing.large))
        container.add_item(ui.Section(
            ui.TextDisplay('Alternate versions exist for this character'),
            accessory=create_content_button(await switch_char_ui(alt_chars, language, cs), 'Switch', save_state=True)
        ))

    # Version
    container.add_item(ui.TextDisplay(f'-# Master Version - {char_resp.version}'))
    
    return container

async def char_info_embed(char_data: schemas.APIResponse[schemas.Character], skill_data: schemas.APIResponse[schemas.Skills], cs: schemas.CommonStrings):
    embed = BaseEmbed(char_data.version, color=Color.green())
    char = char_data.data
    async with SessionAA() as session:
        element_emoji = await to_emoji(session, char.element)
        job_emoji = await to_emoji(session, char.job)

    embed.title=character_title(char.title, char.name)
    embed.description=(
        f'**Id:** {char.char_id}\n'
        f'**Element:** {element_emoji}{cs.element[char.element]}\n'
        f'**Base Rarity:** {enums.CharacterRarity(char.rarity).name}\n'
        f'**Class:** {job_emoji}{cs.job[char.job]}\n'
        f'**Base Speed:** {char.speed}\n'
        f'**UW:** {char.uw}\n'
    )

    if skill_data:
        skills = skill_data.data

        skill_text = ''
        for skill in skills.actives:
            skill_text += f'{skill.name} | **CD:** {skill.max_cooltime}\n'
        embed.add_field(
            name='__Active Skills__',
            value=skill_text,
            inline=False
        )

        skill_text = ''
        for skill in skills.passives:
            if skill.name and skill.name != '*':
                skill_text += f'{skill.name}\n'
        embed.add_field(
            name='__Passive Skills__',
            value=skill_text,
            inline=False
        )
    else:  # Case where skill data is not avaliable when basic info is
        embed.add_field(
            name ='__Skill Data__',
            value='*Currently unavaliable*',
            inline=False
        )

    image_link = RAW_ASSET_BASE + f'Characters/Sprites/CHR_{char.char_id:06}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

def profile_embed(profile_data: schemas.APIResponse[schemas.Profile], name: schemas.Name):
    profile = profile_data.data
    name = character_title(name.title, name.name)

    description = (
        f'**Id:** {profile.char_id}\n'
        f'**Birthday:** {profile.birthday//100}/{profile.birthday%100}\n'
        f'**Blood Type:** {profile.blood_type.name}\n'
        f'**Height:** {profile.height}cm\n'
        f'**Weight:** {profile.weight}kg\n\n'
        f'**Song by:** {profile.vocalJP}\n'
        # f'**Vocal (US):** {profile.vocalUS}\n'
        f'**CV (JP):** {profile.voiceJP}\n'
        f'**CV (US):** {profile.voiceUS}\n'
    )

    return BaseEmbed(
        profile_data.version,
        title=name,
        description=description,
        color=Color.green()
    ).set_thumbnail(url=CHARACTER_THUMBNAIL.format(char_id=profile.char_id, qlipha=False))

async def voiceline_view(
    interaction: Interaction,
    voiceline_data: schemas.APIResponse[schemas.CharacterVoicelines],
    profile_data: schemas.APIResponse[schemas.Profile],
    language: enums.LanguageOptions):
    h = HTML2Text()
    voicelines = voiceline_data.data
    profile = profile_data.data
    
    name = await api.fetch_name(voicelines.char_id, language)

    title = f'{possessive_form(character_title(name.title, name.name))} Voicelines'
    embeds = []
    for batch in batched((voiceline for voiceline in voicelines.voicelines if voiceline.subtitle), 10):
        description = StringIO()
        for voiceline in batch:
            description.write(f'**{voiceline.button_text}**\n{h.handle(voiceline.subtitle)}')
        embeds.append(BaseEmbed(
            voiceline_data.version,
            title=title,
            description=description.getvalue(),
            color=Color.gold()
        ))
    if profile.gacha_message:
        embeds[-1].description += f'**Gacha Message 1**\n{h.handle(profile.gacha_message)}'
    
    return ButtonView(interaction.user, {'default': embeds})

async def memory_view(interaction: Interaction, memory_data: schemas.APIResponse[schemas.CharacterMemories], language: enums.LanguageOptions):
    h = HTML2Text()
    memories = memory_data.data
    name = await api.fetch_name(memories.char_id, language)
    
    title = f'{possessive_form(character_title(name.title, name.name))} Memories'
    embeds = []
    for memory in memories.memories:
        description = f'**{memory.title}**\n{h.handle(memory.text)}'
        # jp_url = MOONHEART_ASSET_MEMORY.format(
        #     region='JP',
        #     char_id=memories.char_id,
        #     episode_id=memory.episode_id
        # )
        # us_url = MOONHEART_ASSET_MEMORY.format(
        #     region='US',
        #     char_id=memories.char_id,
        #     episode_id=memory.episode_id
        # )
        
        embeds.append(
            BaseEmbed(
                memory_data.version,
                title=title,
                description=description,
                color=Color.orange()
            # ).add_field(
            #     name='Voice',value=f'[JP]({jp_url})|[US]({us_url})', inline=False
            ).set_thumbnail(url=CHARACTER_THUMBNAIL.format(char_id=memories.char_id, qlipha=False))
        )
    return ButtonView(interaction.user, {'default': embeds})

