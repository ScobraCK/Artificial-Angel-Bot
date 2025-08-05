import re
from typing import Literal

from table2ascii import Alignment, PresetStyle, table2ascii as t2a
from common.enums import BattleParameter, Server
from common.schemas import Parameter, CommonStrings

PERCENTAGE_PARAMS = [
    BattleParameter.CRIT_DMG_BOOST,
    BattleParameter.M_CRIT_DMG_CUT,
    BattleParameter.P_CRIT_DMG_CUT,
    BattleParameter.COUNTER,
    BattleParameter.HP_DRAIN
]

def remove_linebreaks(text: str):
    return text.replace('<br>', ' ')

def remove_html(text: str):
    clean = re.compile('<.*?>')
    text = remove_linebreaks(text)
    return re.sub(clean, '', text)

def possessive_form(word: str) -> str:
    return f"{word}'s" if not word.endswith('s') else f"{word}'"

def character_title(title: str, name: str):
    if title:
        return f'[{title}] {name}'
    return name

def calc_buff(base: int, multipliers: list[int]):
    result = base
    for mult in multipliers:
        result += int(base*mult/100)
    return result

def human_format(num: int)->str:
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T'][magnitude])

def decimal_format(num: int)->str:
    decimal = 1 if num % 10 == 0 else 2
    return f'{num/100:.{decimal}f}'

def param_string(param: Parameter, cs: CommonStrings):
    param_type = param.category
    if param_type == 'Base':
        param_type_dict = cs.base_param
    else:
        param_type_dict = cs.battle_param
    if param.change_type == 1:
        if param_type == 'Battle' and param.type in PERCENTAGE_PARAMS:
            return f'{param_type_dict[param.type]} {decimal_format(param.value)}%'
        else:
            return f'{param_type_dict[param.type]} {param.value:,}'
    elif param.change_type == 2:
        return f'{param_type_dict[param.type]} {param.value/100:.1f}%'
    else:  # [BattleParameterCharacterLevelConstantMultiplicationAddition]
        return f'{param_type_dict[param.type]} Chara. Lv×{param.value:,}'

def to_world_id(server: Server, world: int):
    return int(f'{server}{world:03}')

def from_world_id(worldid: int) -> tuple[Server, int]:
    if isinstance(worldid, str):
        worldid = int(worldid)
    server = Server(worldid // 1000)
    world = worldid % 1000
    return server, world

def to_quest_id(quest: str)->int:
    '''
    Converts [chapter]-[stage] to quest id
    returns None if invalid

    Max stages
    Chapter 1: 12
    Chapter 2: 20
    Chapter 3: 24
    Chapter 4+: 28
    Chapter 27+: 40,
    Chapter 35+: 60
    '''
    if quest.isnumeric():
        return int(quest)
    try:
        chap, stage = tuple(map(int, (re.split('[ -/]', quest, maxsplit=2))))
    except ValueError:
        return None
    if not (0 < stage):
        return None
    if chap == 1:
        return (stage if stage <= 12 else None)
    elif chap == 2:
        return (stage + 12 if stage <= 20 else None)
    elif chap == 3:
        return (stage + 32 if stage <= 24 else None)
    elif chap < 27:
        return ((chap-2) * 28 + stage if stage <= 28 else None) # 1-3 is 28*2 stages
    elif chap < 35:
        return (700 + (chap-27)*40 + stage if stage <= 40 else None) # 26-28 is 700
    else:
        return (1020 + (chap-35)*60 + stage if stage <= 60 else None) # 25-40 is 1020


def from_quest_id(quest_id: int)->str:
    '''
    Converts quest id to [chapter]-[stage]

    Max stages
    Chapter 1: 12
    Chapter 2: 20
    Chapter 3: 24
    Chapter 4+: 28
    Chapter 27+: 40,
    Chapter 35+: 60
    '''
    if isinstance(quest_id, str):
        quest_id = int(quest_id)
        
    if quest_id > 1020:
        chap, stage = divmod(quest_id-1020, 60)
        if stage==0:
            chap += -1
            stage = 60
        return f"{chap+35}-{stage}"
    elif quest_id > 700:
        chap, stage = divmod(quest_id-700, 40)
        if stage==0:
            chap += -1
            stage = 40
        return f"{chap+27}-{stage}"
    elif quest_id > 56:
        chap, stage = divmod(quest_id, 28)
        if stage==0:
            chap += -1
            stage = 28
        return f"{chap+2}-{stage}"
    elif quest_id > 32: # chapter 3
        return f"3-{quest_id-32}"
    elif quest_id > 12: # chapter 2
        return f"2-{quest_id-12}"
    else: # chapter 1
        return f"1-{quest_id}"


def make_table(data, header: list[str], style=Literal['thin_compact', 'ascii_simple'], cell_padding=1):
    style_dict = {
        'thin_compact': PresetStyle.thin_compact,
        'ascii_simple': PresetStyle.ascii_simple
    }
    return t2a(
        header=header,
        body=data,
        style=style_dict[style],
        alignments=Alignment.LEFT,
        cell_padding=cell_padding
    )
