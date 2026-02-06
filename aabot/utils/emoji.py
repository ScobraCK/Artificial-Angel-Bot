from enum import Enum

from async_lru import alru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.crud.character import get_character
from aabot.crud.emoji import get_emoji
from aabot.utils.api import fetch_name
from aabot.utils.utils import character_title
from common.database import SessionAA
from common.enums import Element, Language
from common.schemas import Character, ItemBase, EquipmentFragment, QuickTicket, ActiveSkill, PassiveSkill, Rune

_emoji_cache = {}

def _get_emoji_name(
        obj: Character|ItemBase|EquipmentFragment|QuickTicket|ActiveSkill|PassiveSkill|Enum|str
) -> str:
    if isinstance(obj, Enum):
        return emoji_list.get(obj.name.lower())
    elif isinstance(obj, str):  
        return emoji_list.get(obj.lower())
    elif isinstance(obj, Rune):
        return f'SPH_{obj.icon:04}'  # TODO add other runes
    elif isinstance(obj, EquipmentFragment):
        return 'fragment'
    elif isinstance(obj, QuickTicket):
        if obj.item_id <= 5:
            return emoji_list['gold']
        elif obj.item_id <= 10:
            return emoji_list['green_orb']
        elif obj.item_id <= 15:
            return emoji_list['red_orb']
        else:
            return f'Item_{obj.icon:04}'  # TODO add growth set
    elif isinstance(obj, ItemBase):
        return f'Item_{obj.icon:04}'
    else:
        return obj.name  # TODO handle other types later

async def to_emoji(
        session: AsyncSession,
        obj: Character|ItemBase|EquipmentFragment|QuickTicket|ActiveSkill|PassiveSkill|Enum|str
) -> str:
    name = _get_emoji_name(obj)
    if name in _emoji_cache:
        return _emoji_cache[name]

    emoji = await get_emoji(session, name)

    if emoji:
        _emoji_cache[name] = f'<:{emoji.name}:{emoji.id}>'
        if isinstance(obj, QuickTicket):
            return f'{_emoji_cache[name]}({obj.hours}h)'
        else:
            return _emoji_cache[name]
    elif isinstance(name, str) and name.startswith(':') and name.endswith(':'):  # default emoji
        _emoji_cache[name] = name
        return name
    else:
        # don't cache in case emoji is added
        if isinstance(obj, str):
            return obj
        else:
            return obj.name

@alru_cache()
async def char_ele_emoji(char_id: int) -> str:
    async with SessionAA() as session:
        char = await get_character(session, char_id)
        if not char:
            raise ValueError(f'Character with id {char_id} not found in characters table')
        emoji = await to_emoji(session, Element(char.element))
    return emoji

async def character_string(id: int, language: Language) -> str:
    if id == 0:
        return '???'
    element = await char_ele_emoji(id)
    name = await fetch_name(id, language)
    return f'{element}{character_title(name.title, name.name)}'

emoji_list = {
    # items
    'dia': 'Item_0009',
    'gold': 'Item_0010',
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
    'weapon_1': 'equipment_weapon_warrior_01',
    'weapon_2': 'equipment_weapon_sniper_01',
    'weapon_4': 'equipment_weapon_sorcerer_01',
    'sword': 'equipment_weapon_warrior_01',
    'pistol': 'equipment_weapon_sniper_01',
    'tome': 'equipment_weapon_sorcerer_01',
    # misc
    'fragment': 'fragment',
    'star1': 'battle_difficulty_01',
    'star2': 'battle_difficulty_02',
    'x': 'close',
    'check': 'check_03',
    'resonance': 'CSK_000035004',
    'down': 'arrow_parameter_down',
    'up': 'arrow_parameter_up',
}
