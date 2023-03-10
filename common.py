# from typing import List, TypedDict
from enum import Enum

############
# Character id
############

# used to limit id and faster id search
id_list = {
    1: 'Monica',
    2: 'Illya',
    3: 'Iris',
    4: 'Loki',
    5: 'Soltina',
    6: 'Amleth',
    7: 'Fenrir',
    8: 'Florence',
    9: 'Sonya',
    10: 'Moddey',
    11: 'Charlotte',
    12: 'Arianrhod',
    13: 'Theodora',
    14: 'Petra',
    15: 'Sabrina',
    16: 'Freesia',
    17: 'Amour',
    18: 'Rean',
    19: 'Belle',
    20: 'Dian',
    21: 'Shizu',
    22: 'Zara',
    23: 'Rosalie',
    24: 'Libra',
    25: 'Ivy',
    26: 'Merlyn',
    27: 'Cordie',
    28: 'Nina',
    29: 'Mertillier',
    30: 'Luke',
    31: 'Garmr',
    32: 'Skuld',
    33: 'Cherna',
    34: 'Soteira',
    35: 'Mimi',
    36: 'Tropon',
    37: 'Hathor',
    38: 'Olivia',
    39: 'Primavera',
    40: 'Carol',
    41: 'Natasha',
    42: 'Fortina',
    43: 'Cerberus',
    44: 'Rusalka',
    45: 'Elfriede',
    46: 'Lunalynn',
    47: 'Valeriede',
    48: 'A.A.',
    49: 'Ophelia',
    50: 'Armstrong',
    51: 'Sophia'
}
MAX_CHAR_ID = len(id_list)

# for use in name matching
char_list = {
    'monica': 1,
    'illya': 2,
    'iris': 3,
    'loki': 4,
    'soltina': 5,
    'amleth': 6,
    'fenrir': 7,
    'florence': 8,
    'sonya': 9,
    'viking': 9,
    'moddey': 10,
    'charlotte': 11,
    'arianrhod': 12,
    'theodora': 13,
    'petra': 14,
    'sabrina': 15,
    'freesia': 16,
    'amour': 17,
    'rean': 18,
    'belle': 19,
    'dian': 20,
    'evade': 20,
    'shizu': 21,
    'zara': 22,
    'rosalie': 23,
    'libra': 24,
    'ivy': 25,
    'red': 25,
    'merlyn': 26,
    'cordie': 27,
    '999': 27,
    'nina': 28,
    'mertillier': 29,
    'hakase': 29,
    'luke': 30,
    'garmr': 31,
    'skuld': 32,
    'cherna': 33,
    'soteira': 34,
    'dezzy': 34,
    'macaron': 34,
    'mimi': 35,
    'cheese': 35,
    'tropon': 36,
    'hathor': 37,
    'olivia': 38,
    'primavera': 39,
    'carol': 40,
    'natasha': 41,
    'the witch of mourning flowers': 41,
    'fortina': 42,
    'the witch of sacred swords': 42,
    'cerberus': 43,
    'the witch of wailing lightning': 43,
    'rusalka': 44,
    'the witch of torrential sorrow': 44,
    'elfriede': 45,
    'the witch of longinus': 45,
    'lunalynn': 46,
    'the witch of snowy illusions': 46,
    'valeriede': 47,
    'the witch of conflagration': 47,
    'aa': 48,
    'a.a.': 48,
    'best girl': 48,
    'the witch of rust': 48,
    'ophelia': 49,
    'the witch of fallen crystals': 49,
    'armstrong': 50,
    'the witch of lost souls': 50,
    'sophia': 51,
    # japanese
    '?????????': 1, 
    '?????????': 2,
    '????????????': 3,
    '??????': 4,
    '??????????????????': 5,
    '???????????????': 6,
    '???????????????': 7,
    '??????????????????': 8,
    '????????????': 9,
    '?????????': 10,
    '??????????????????': 11,
    '?????????????????????': 12,
    '????????????': 13,
    '?????????': 14,
    '????????????': 15,
    '???????????????': 16,
    '????????????': 17,
    '?????????': 18,
    '??????': 19,
    '????????????': 20,
    '??????': 21,
    '??????': 22,
    '????????????': 23,
    '?????????': 24,
    '????????????': 25,
    '????????????': 26,
    '????????????': 27,
    '?????????': 28,
    '??????????????????': 29,
    '?????????': 30,
    '?????????': 31,
    '????????????': 32,
    '????????????': 33,
    '????????????': 34,
    '??????': 35,
    '????????????': 36,
    '????????????': 37,
    '???????????????': 38,
    '?????????????????????': 39,
    '?????????': 40,
    '???????????????': 41,
    '??????????????????': 42,
    '???????????????': 43,
    '???????????????': 44,
    '??????????????????': 45,
    '???????????????': 46,
    '??????????????????': 47,
    '????????????': 48,
    '??????????????????': 49,
    '????????????????????????': 50,
    '????????????': 51
}

############
# Dictionary maps
############

# character basic info
basic_info = ["Id", "Element", 'Base Rarity', 'Class', 'Normal Attack', 'Base Speed','UW']

normal_skills = {
    101: 'Physical',
    102: 'Magical'
}

souls = {
    1: 'Azure',
    2: 'Crimson',
    3: 'Emerald',
    4: 'Amber',
    5: 'Radiant',
    6: 'Chaos'
}

char_rarity = {
    1: 'N',
    2: 'R',
    4: 'R+',
    8: 'SR',
    16: 'SR+',
    32: 'SSR',
    64: 'SSR+',
    128: 'UR',
    256: 'UR+',
    512: 'LR',
    1024: 'LR+1',
    2048: 'LR+2',
    4096: 'LR+3',
    8192: 'LR+5',
    16384: 'LR+6',
}

equip_rarity = {
    1: 'D',
    2: 'C',
    4: 'B',
    8: 'A',
    16: 'S',
    32: 'R',
    64: 'SR',
    128: 'SSR',
    256: 'UR',
    512: 'LR'
}

job_map = {
    1: 'Warrior',
    2: 'Sniper',
    4: 'Sorcerer'
}

uw_rarity_skill_map = {
    128: "Description1Key",
    256: "Description2Key",
    512: "Description3Key"
}

uw_rarity_list = ['SSR', 'UR', 'LR']

base_parameter_map = {
    'STR': 'Muscle',
    'DEX': 'Energy',
    'MAG': 'Intelligence',
    'STA': 'Health'
}

battle_parameter_map1 = {
    'HP': "HP",
    'ATK': "AttackPower",
    'DEF': "Defense",
    'DEF Break': "DefensePenetration",
    'SPD': "Speed",
}

battle_parameter_map2 = {
    'PM.DEF Break': "DamageEnhance",
    'P.DEF': "PhysicalDamageRelax",
    'M.DEF': "MagicDamageRelax",
    'ACC': "Hit",
    'EVD': "Avoidance",
    'CRIT': "Critical",
    'CRIT RES': "CriticalResist",
    'CRIT DMG Boost': "CriticalDamageEnhance",
    'P.CRIT DMG Cut': "MagicCriticalDamageRelax",
    'M.CRIT DMG Cut': "PhysicalCriticalDamageRelax",
    'Debuff ACC': "DebuffHit",
    'Debuff RES': "DebuffResist",
    'Counter': "DamageReflect",
    'HP Drain': "HpDrain"
}

battle_parameter_left = ['PM.DEF Break', 'ACC', 'CRIT', 'CRIT DMG Boost', 'Debuff ACC', 'Counter']
battle_parameter_right = ['M.DEF', 'M.CRIT DMG Cut']
battle_parameter_percentage = ['CRIT DMG Boost', 'P.CRIT DMG Cut', 'M.CRIT DMG Cut', 'Counter', 'HP Drain']

# limited events
event_type = {
    1: {
        'name': 'Tower Release Event',
        'description': 'For a limited time, all Souls in the Tower of Infinity will be unlocked!'}
}

############
# Others
############

# for images
raw_asset_link_header='https://raw.githubusercontent.com/ScobraCK/MementoMori-data/main/Assets/'


############
# Enums
############
class Skill_Enum(Enum):
    Active = '[SkillCategoryActive]'
    Passive = '[SkillCategoryPassive]'

# language Enum
class Language(Enum):
    English = 'enUS'
    Japanese = 'jaJP'
    Korean = 'koKR'
    Taiwanese = 'zhTW'

# timezones (hours in timedelta)
class Server(Enum):
    NA = -7
    JP_KR = 9
    EU_GLOBAL = 1
    ASIA = 8

# Towers
class Tower(Enum):
    Infinity = 1
    Azure = 2
    Crimson = 3
    Emerald = 4
    Amber = 5