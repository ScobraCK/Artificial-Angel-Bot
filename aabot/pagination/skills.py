from io import StringIO
from itertools import chain

from discord import Color, Interaction

from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import DropdownView, MixedView
from aabot.utils.assets import RAW_ASSET_BASE
from aabot.utils.emoji import level_emoji, rarity_emoji
from aabot.utils.utils import character_title, possessive_form, remove_linebreaks
from common import enums, schemas


def skill_description(skills: list[schemas.ActiveSkill|schemas.PassiveSkill], uw_desc: schemas.UWDescriptions, uw_name: str, include_name=True) -> str:
    if not skills:
        return None

    description = StringIO()

    for skill in skills:
        if include_name:
            if skill.name == '*':
                if skill.skill_infos[0].uw_rarity == 0:  # Special skills such as Rosalie(SR), Paladea
                    continue
                else:
                    name = f'### {uw_name}'  # UW passive
            else:
                name = f'### {skill.name}'
            if isinstance(skill, schemas.ActiveSkill):
                name += f' | CD: {skill.max_cooltime}'
            description.write(f'{name}\n')

        for info in skill.skill_infos:
            if (rarity := enums.ItemRarity(info.uw_rarity).name):  # Convert to rarity str [SSR, UR, LR]
                uw_description = getattr(uw_desc, rarity) if uw_desc else 'Description unavaliable.'
                description.write(f"**{rarity} Weapon**{rarity_emoji.get(rarity)}\n{remove_linebreaks(uw_description)}\n")
            else:
                description.write(
                    f'**Skill Lv.{info.order_number}**{level_emoji.get(info.order_number)} (Lv.{info.level})\n'
                    f'{remove_linebreaks(info.description)}\n'
                )
            description.write('\n')

    return description.getvalue()

def uw_skill_description(uw: schemas.UWDescriptions, uw_name: str = None) -> str: 
    if not uw:
        return None
    description = StringIO()
    if uw_name:
        description.write(f'__{uw_name}__\n')  # Given for skills
    for rarity in ('SSR', 'UR', 'LR'):
        description.write(f"__**{rarity} Weapon**__{rarity_emoji.get(rarity)}\n{getattr(uw,(rarity))}\n")
    
    return description.getvalue()

def skill_view(
    interaction: Interaction,
    skill_data: schemas.APIResponse[schemas.Skills],
    char_data: schemas.APIResponse[schemas.Character]):
    skills = skill_data.data
    char = char_data.data
    embed_dict = {}

    title_text = f'{possessive_form(character_title(char.title, char.name))}'
    icon_url = f'{RAW_ASSET_BASE}Characters/Sprites/CHR_{char.char_id:06}_00_s.png'

    embed_dict['Active'] = [
        BaseEmbed(
            skill_data.version,
            title=f'{title_text} Active Skills',
            description=skill_description(skills.actives, skills.uw_descriptions, char.uw),
            color=Color.blue()
        ).set_thumbnail(url=icon_url)
    ]

    if skills.passives:
        embed_dict['Passive'] = [
            BaseEmbed(
                skill_data.version,
                title=f'{title_text} Passive Skills',
                description=skill_description(skills.passives, skills.uw_descriptions, char.uw),
                color=Color.blue()
            ).set_thumbnail(url=icon_url)
        ]
    
    if skills.uw_descriptions:
        embed_dict['Unique Weapon'] = [
            BaseEmbed(
                skill_data.version,
                title=f'{title_text} Unique Weapon',
                description=uw_skill_description(skills.uw_descriptions, char.uw),
                color=Color.blue()
            ).set_thumbnail(url=icon_url)
        ]

    return DropdownView(interaction.user, embed_dict, 'Active')


def skill_detail_view(
    interaction: Interaction,
    skill_data: schemas.APIResponse[schemas.Skills],
    char_data: schemas.APIResponse[schemas.Character]):
    skills = skill_data.data
    char = char_data.data
    embed_dict = {}

    for skill in chain(skills.actives, skills.passives):
        embeds = []
        icon_url = RAW_ASSET_BASE + f"Characters/Skills/CSK_00{skill.id:07}.png"
        description = skill_description([skill], skills.uw_descriptions, char.uw, False)
        
        if skill.name == '*' and skill.skill_infos[0].uw_rarity == 0:  # Special skills such as Rosalie(SR), Paladea
            title = 'Special Skill'
        else:
            title = skill.name
        
        if isinstance(skill, schemas.ActiveSkill):
            main_description = f'**CD:** {skill.max_cooltime}\n\n{description}'
        else:
            main_description = description
        
        
        embeds.append( # Main Embed
            BaseEmbed(
                skill_data.version,
                title=title,
                description=main_description,
                color=Color.blue()
            ).set_thumbnail(url=icon_url)
        )

        # Skill level details
        for info in skill.skill_infos:
            uw_rarity_str = enums.ItemRarity(info.uw_rarity).name
            # Common
            if uw_rarity_str:
                if skills.uw_descriptions:
                    info_description = f'{getattr(skills.uw_descriptions, uw_rarity_str)}\n\n'
                else:  # Unreleased char
                    info_description = 'Description unavaliable.\n\n'
            else:
                info_description = f'{info.description}\n\n'

            info_description += (
                '**Details**\n' 
                f'```json\n'
                f"Order Number: {info.order_number}\n"
                f"Character Level: {info.level}\n"
                f"Equipment Rarity: {uw_rarity_str}```"
            )
            # Active
            if isinstance(skill, schemas.ActiveSkill):
                info_description += (
                    '**Cooldown Info**\n'
                    f'```json\n'
                    f'Init CD: {skill.init_cooltime}\n'
                    f'Max CD: {skill.max_cooltime}```'
                    '**Subskills**\n'
                    f"```json\n{'\n'.join(map(str, info.subskill))}```"
                )
            # Passive
            else:
                info_description += '**Subskills**\n'
                subskills: list[schemas.PassiveSubSkill] = info.subskill
                for sub in subskills:
                    info_description += (
                        '```json\n'
                        f'Passive Trigger: {sub.trigger}\n'
                        f'Initial CD: {sub.init_cooltime}\n'
                        f'Max CD: {sub.max_cooltime}\n'
                        f'Group Id: {sub.group_id}\n'
                        f'Subskill Id: {sub.subskill_id}```'
                    )       
            embeds.append(
                BaseEmbed(
                    skill_data.version,
                    title=title,
                    description=info_description,
                    color=Color.blue()
                ).set_thumbnail(url=icon_url)
            )
        embed_dict[title] = embeds
    
    return MixedView(interaction.user, embed_dict, key=skills.actives[0].name)
