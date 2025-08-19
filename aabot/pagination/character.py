from asyncio import gather
from io import StringIO
from itertools import batched

from discord import Color, Interaction
from html2text import HTML2Text

from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import ButtonView, MixedView
from aabot.utils.api import fetch_name
from aabot.utils.assets import RAW_ASSET_BASE, CHARACTER_THUMBNAIL, MOONHEART_ASSET_MEMORY
from aabot.utils.command_utils import LanguageOptions
from aabot.utils.emoji import to_emoji, character_string
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.utils import character_title, calc_buff, param_string, possessive_form
from common import enums, schemas
from common.database import SessionAA

def id_list_view(interaction: Interaction, name_data: schemas.APIResponse[dict[int, schemas.Name]]):
    names = name_data.data.values()
    
    embeds = []
    for batch in batched(names, 50):
        description = StringIO()
        for name in batch:
            description.write(f"{name.char_id}: {character_title(name.title, name.name)}\n")
        embeds.append(
            BaseEmbed(
                name_data.version,
                title='Character Id',
                color=Color.green(),
                description=description.getvalue()
            )
        )
    
    return ButtonView(interaction.user, {'default': embeds})

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

def speed_view(
    interaction: Interaction,
    char_data: schemas.APIResponse[list[schemas.CharacterDBModel]],
    name_data: schemas.APIResponse[dict[int, schemas.Name]],
    add: int, buffs: list[int]=None):
    speed_list = reversed(char_data.data)
    
    if add or buffs:
        header = '__No.__ __Character__ __Speed__ __(Base)__\n'
    else:
        header = '__No.__ __Character__ __Speed__\n'

    embeds = []
    i = 1
    for batch in batched(speed_list, 50):
        description = StringIO()
        for char in batch:
            name = name_data.data.get(char.id)
            char_name = character_title(name.title, name.name) if name else '[Undefined]'
            if add or buffs:
                speed = calc_buff(char.speed+add, buffs) if buffs else (char.speed+add)
                description.write(f'**{i}.** {char_name} {speed} ({char.speed})\n')
            else:
                description.write(f'**{i}.** {char_name} {char.speed}\n')
            i += 1

        embed = BaseEmbed(char_data.version, title='Character Speeds', description=f'{header}{description.getvalue()}')
        embed.add_field(
            name='Bonus Parameters',
            value=f'Rune Bonus: {add}\nBuffs: {buffs}',
            inline=False
        )

        embeds.append(embed)
    
    view = ButtonView(interaction.user, {'default': embeds})
    return view

async def voiceline_view(
    interaction: Interaction,
    voiceline_data: schemas.APIResponse[schemas.CharacterVoicelines],
    profile_data: schemas.APIResponse[schemas.Profile],
    language: LanguageOptions):
    h = HTML2Text()
    voicelines = voiceline_data.data
    profile = profile_data.data
    
    name = await fetch_name(voicelines.char_id, language)

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

async def memory_view(interaction: Interaction, memory_data: schemas.APIResponse[schemas.CharacterMemories], language: LanguageOptions):
    h = HTML2Text()
    memories = memory_data.data
    name = await fetch_name(memories.char_id, language)
    
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

async def arcana_basic_text(arcana: schemas.Arcana, cs: schemas.CommonStrings, language: LanguageOptions):
    text = StringIO()

    text.write(f'**{arcana.name}**')
    if arcana.required_level > 0:
        text.write(f' ({cs.common.get('arcana level limit', 'Unlocked at Party Lv 300.')})')
    text.write('\n')
    text.write(f'{cs.common.get('characters', 'Characters')}: ')

    names = []
    for char in arcana.characters:
        char_str = await character_string(char, language)
        names.append(char_str)
    text.write(', '.join(names))

    bonus = []
    text.write('\n```\n')
    lr_level = next(filter(lambda x: x.rarity == enums.CharacterRarity.LR, arcana.levels))
    if lr_level.level_bonus:
        bonus.append(f'{cs.common.get('arcana bonus level', 'Max Party Lv')}: {lr_level.level_bonus}')
    for param in lr_level.parameters:
        bonus.append(param_string(param, cs))
    text.write('\n'.join(bonus))
    text.write('```\n')

    return text.getvalue()

async def arcana_detail_text(arcana: schemas.Arcana, cs: schemas.CommonStrings, language: LanguageOptions):
    text = StringIO()
    text.write(f'**Required party level:** {arcana.required_level}\n')
    text.write(f'**{cs.common.get('characters', 'Characters')}:**\n')
    names = []
    for char in arcana.characters:
        char_str = await character_string(char, language)
        names.append(f'- {char_str}')
    text.write('\n'.join(names))
    text.write('\n\n')

    async def level_text(level: schemas.ArcanaLevel):
        text_ = StringIO()
        ic = ItemCounter(language)
        text_.write(f'**{cs.common.get('arcana', 'Arcana')} Lv {level.level}**\n')
        text_.write(f'**Rarity:** {level.rarity.name.replace('Plus', '+')}\n')
        ic.add_items(level.reward)
        items = await ic.get_total_strings()
        text_.write(f'**Reward:** {', '.join(items)}\n')

        bonus = []
        text_.write('```\n')
        if level.awaken_bonus:
            bonus.append(f'{cs.common.get('arcana awaken', 'Arcana Group Max Awaken.')}  {level.awaken_bonus}')

        if level.rarity >= enums.CharacterRarity.LR and level.parameters:
            bonus.append(f'{cs.common.get('arcana target', 'Enhanced Targets')}: {cs.common.get('arcana target all', 'All Characters')}')
        else:
            bonus.append(f'{cs.common.get('arcana target', 'Enhanced Targets')}: {cs.common.get('arcana target group', 'Arcana Group')}')
        
        if level.level_bonus:
            bonus.append(f'{cs.common.get('arcana bonus level', 'Max Party Lv')}: {level.level_bonus}')

        for param in level.parameters:
            bonus.append(param_string(param, cs))
        text_.write('\n'.join(bonus))
        text_.write('```')
        return text_.getvalue()

    text.write('\n'.join(await gather(*[level_text(level) for level in arcana.levels])))

    return text.getvalue()
    
async def arcana_view(
    interaction: Interaction,
    arcana_data: schemas.APIResponse[list[schemas.Arcana]],
    cs: schemas.CommonStrings,
    language: LanguageOptions
):
    arcanas = arcana_data.data

    if len(arcanas) > 10:
        await interaction.response.defer(thinking=True)

    embed_dict = {
        'Basic': [],
        'Detailed': []
    }
    for arcana_batch in batched(arcanas, 5):
        basic_text = StringIO()
        for arcana in arcana_batch:
            basic_text.write(await arcana_basic_text(arcana, cs, language))
            embed_dict['Detailed'].append(
                BaseEmbed(
                    arcana_data.version,
                    title=arcana.name,
                    description=await arcana_detail_text(arcana, cs, language),
                    color=Color.purple()
                )
            )

        embed_dict['Basic'].append(
            BaseEmbed(
                arcana_data.version,
                title=cs.common.get('arcana', 'Arcana'),
                description=basic_text.getvalue(),
                color=Color.purple()
            ).set_footer(text='Arcana values shown for LR')
        )
    
    return MixedView(interaction.user, embed_dict, 'Basic')
