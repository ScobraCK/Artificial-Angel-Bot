from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from aabot.crud.emoji import get_emoji
from common.schemas import Character, ItemBase, EquipmentFragment, ActiveSkill, PassiveSkill, Rune

_emoji_cache = {}

def _get_emoji_name(obj: Character|ItemBase|ActiveSkill|PassiveSkill) -> str:
    if isinstance(obj, Rune):
        return f'SPH_{obj.icon:04}'
    elif isinstance(obj, ItemBase):
        return f'Item_{obj.icon:04}'
    else:
        return obj.name  # TODO handle other types later

async def to_emoji(session: AsyncSession, obj: Character|ItemBase|EquipmentFragment|ActiveSkill|PassiveSkill|Enum|str) -> str:
    name = None
    # manual emoji list check
    if isinstance(obj, Enum):
        name = emoji_list.get(obj.name.lower())
    elif isinstance(obj, str):  
        name = emoji_list.get(obj.lower())
    elif isinstance(obj, EquipmentFragment):
        name = 'fragment'
    else:
        name = _get_emoji_name(obj)

    if name in _emoji_cache:
        return _emoji_cache[name]

    emoji = await get_emoji(session, name)

    if emoji:
        _emoji_cache[name] = f'<:{emoji.name}:{emoji.id}>'
        return _emoji_cache[name]
    elif name:  # default emoji
        _emoji_cache[name] = name
        return name
    else:
        # don't cache in case emoji is added
        if isinstance(obj, str):
            return obj
        else:
            return obj.name

emoji_list = {
    # items
    'dia': 'Item_0009',
    'green_orb': 'Item_0015',
    'red_orb': 'Item_0016',
    'water': 'Item_0017',
    'red_pot': 'Item_0018',
    'rune_ticket': 'Item_0039',
    'ioc': 'Item_0054',
    'rune': 'Item_0058',
    'iosg': 'Item_0121',
    'fleeting': 'Item_0112',
    'fleeting_s': 'Item_0112_S',
    'eminence': 'Item_0217',
    # stats (rune)
    'sta': 'SPH_1003',
    'mag': 'SPH_0303',
    'spd': 'SPH_0903',
    'dex': 'SPH_0203',
    'str': 'SPH_0103',
    # stats (icon)
    'atk': 'battle_report_offense',
    'def': 'battle_report_defense',
    'hp': 'battle_report_recovery',
    # soul
    'all': 'element_0',
    'azure': 'element_1',
    'crimson': 'element_2',
    'emerald': 'element_3',
    'amber': 'element_4',
    'radiance': 'element_5',
    'chaos': 'element_6',
    # rarity diamond
    'd': 'diamond_N',
    'c': 'diamond_N',
    'b': 'diamond_N',
    'a': 'diamond_N',
    's': 'diamond_S',
    'n': 'diamond_N',
    'r': ':small_blue_diamond:',  # default emoji
    'sr': ':small_orange_diamond:',  # default emoji
    'ssr': 'diamond_SSR',
    'ur': 'diamond_UR',
    'lr': 'diamond_LR',
    'skill_level_1': ':small_blue_diamond:',  # default emoji
    'skill_level_2': ':small_orange_diamond:',  # default emoji
    'skill_level_3': 'diamond_SSR',
    'skill_level_4': 'diamond_UR',
    # weapon
    # job
    'warrior': 'job_warrior',
    'sniper': 'job_sniper',
    'sorcerer': 'job_sorcerer',
    # equip type icon
    'sub': 'equipment_sub_01',
    'gauntlet': 'equipment_gauntlet_01',
    'helmet': 'equipment_helmet_01',
    'armor': 'equipment_armor_01',
    'shoes': 'equipment_shoes_01',
    'sword': 'equipment_weapon_warrior_01',
    'pistol': 'equipment_weapon_sniper_01',
    'tome': 'equipment_weapon_sorcerer_01',
    # misc
    'fragment': 'fragment',
    'star1': 'battle_difficulty_01',
    'star2': 'battle_difficulty_02',
    'x': 'close',
    'check': 'check_03',
}
