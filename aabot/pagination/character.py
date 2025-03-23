from discord import Color, Interaction
from html2text import HTML2Text
from io import StringIO
from itertools import batched
from typing import List, Dict

import aabot.api.response as resp
from aabot.api.api import fetch_name
from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import ButtonView
from aabot.utils.assets import RAW_ASSET_BASE, CHARACTER_THUMBNAIL, MOONHEART_ASSET_MEMORY
from aabot.utils.enums import Language
from aabot.utils.utils import character_title, calc_buff, possessive_form

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

def id_list_view(interaction: Interaction, name_data: resp.APIResponse[Dict[int, resp.Name]]):
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

def char_info_embed(char_data: resp.APIResponse[resp.Character], skill_data: resp.APIResponse[resp.Skills]):
    embed = BaseEmbed(char_data.version)
    char = char_data.data

    embed.title=character_title(char.title, char.name)
    embed.description=(
        f'**Id:** {char.char_id}\n'
        f'**Element:** {char.element}\n'
        f'**Base Rarity:** {char.rarity}\n'
        f'**Class:** {char.job}\n'
        f'**Attack Type:** {char.attack_type}\n'
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

def speed_view(
    interaction: Interaction,
    char_data: resp.APIResponse[List[resp.CharacterDBModel]],
    name_data: resp.APIResponse[Dict[int, resp.Name]],
    add: int, buffs: List[int]=None):
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
    voiceline_data: resp.APIResponse[resp.CharacterVoicelines],
    profile_data: resp.APIResponse[resp.Profile],
    language: Language):
    h = HTML2Text()
    voicelines = voiceline_data.data
    profile = profile_data.data
    
    name_data = await fetch_name(voicelines.char_id, language)
    name = name_data.data

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

async def memory_view(interaction: Interaction, memory_data: resp.APIResponse[resp.CharacterMemories], language: Language):
    h = HTML2Text()
    memories = memory_data.data
    name_data = await fetch_name(memories.char_id, language)
    name = name_data.data
    
    title = f'{possessive_form(character_title(name.title, name.name))} Memories'
    embeds = []
    for memory in memories.memories:
        description = f'**{memory.title}**\n{h.handle(memory.text)}'
        jp_url = MOONHEART_ASSET_MEMORY.format(
            region='JP',
            char_id=memories.char_id,
            episode_id=memory.episode_id
        )
        us_url = MOONHEART_ASSET_MEMORY.format(
            region='US',
            char_id=memories.char_id,
            episode_id=memory.episode_id
        )
        
        embeds.append(
            BaseEmbed(
                memory_data.version,
                title=title,
                description=description,
                color=Color.orange()
            ).add_field(
                name='Voice',value=f'[JP]({jp_url})|[US]({us_url})', inline=False
            ).set_thumbnail(url=CHARACTER_THUMBNAIL.format(char_id=memories.char_id, qlipha=False))
        )
    return ButtonView(interaction.user, {'default': embeds})
        