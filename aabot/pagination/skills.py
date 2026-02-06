from io import StringIO
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.utils.emoji import to_emoji
from aabot.utils.utils import remove_linebreaks
from common import enums, schemas

async def get_skill_name(skill: schemas.ActiveSkill|schemas.PassiveSkill, uw_name: str) -> str:
    '''Returns None if skill does not have a name.'''
    if skill.name == '*' or not skill.name:
        if skill.skill_infos[0].uw_rarity > 0 and isinstance(skill, schemas.PassiveSkill):
            return uw_name  # UW passive
        else:  # Alt skills such as Rosalie(SR), Paladea.
            return None
    else:
        return skill.name

async def get_skill_text(skill: schemas.ActiveSkill|schemas.PassiveSkill, uw_desc: schemas.UWDescriptions, session: AsyncSession) -> str:
    text = StringIO()
    for info in skill.skill_infos:
        if (rarity := enums.ItemRarity(info.uw_rarity).name):  # Convert to rarity str [SSR, UR, LR]
            uw_description = getattr(uw_desc, rarity) if uw_desc else 'Description unavaliable.'
            text.write(f"**{rarity} Weapon**{await to_emoji(session, rarity)}\n{remove_linebreaks(uw_description)}\n")
        else:
            text.write(
                f'**Skill Lv.{info.order_number}**{await to_emoji(session, f'skill_level_{info.order_number}')} (Lv.{info.level})\n'
                f'{remove_linebreaks(info.description)}\n'
            )
        text.write('\n')

    return text.getvalue()

async def get_uw_skill_text(uw: schemas.UWDescriptions, session: AsyncSession,) -> str: 
    if not uw:
        return None
    text = StringIO()
    for rarity in ('SSR', 'UR', 'LR'):
        text.write(f"__**{rarity} Weapon**__{await to_emoji(session, rarity)}\n{remove_linebreaks(getattr(uw, rarity))}\n")

    return text.getvalue()

async def skill_description(skills: list[schemas.ActiveSkill|schemas.PassiveSkill], uw_desc: schemas.UWDescriptions, uw_name: str, session: AsyncSession, include_name=True) -> str:
    if not skills:
        return None

    description = StringIO()

    for skill in skills:
        if include_name:
            if skill.name == '*' or not skill.name:
                if skill.skill_infos[0].uw_rarity > 0 and isinstance(skill, schemas.PassiveSkill):
                    name = f'### {uw_name}'  # UW passive
                else:  # Skip alt skills such as Rosalie(SR), Paladea
                    continue
            else:
                name = f'### {skill.name}'
            if isinstance(skill, schemas.ActiveSkill):
                name += f' | CD: {skill.max_cooltime}'
            description.write(f'{name}\n')

        for info in skill.skill_infos:
            if (rarity := enums.ItemRarity(info.uw_rarity).name):  # Convert to rarity str [SSR, UR, LR]
                uw_description = getattr(uw_desc, rarity) if uw_desc else 'Description unavaliable.'
                description.write(f"**{rarity} Weapon**{await to_emoji(session, rarity)}\n{remove_linebreaks(uw_description)}\n")
            else:
                description.write(
                    f'**Skill Lv.{info.order_number}**{await to_emoji(session, f'skill_level_{info.order_number}')} (Lv.{info.level})\n'
                    f'{remove_linebreaks(info.description)}\n'
                )
            description.write('\n')

    return description.getvalue()
