# from typing import List, TypedDict
from enum import Enum

# used in slash command limit
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
    50: 'Armstrong'
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
    'shizu': 21,
    'zara': 22,
    'rosalie': 23,
    'libra': 24,
    'ivy': 25,
    'merlyn': 26,
    'cordie': 27,
    'nina': 28,
    'mertillier': 29,
    'hakase': 29,
    'luke': 30,
    'garmr': 31,
    'skuld': 32,
    'cherna': 33,
    'soteira': 34,
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
    'the witch of lost souls': 50
}

# language Enum
class Language(Enum):
    English = 'enUS'
    Japanese = 'jaJP'
    Korean = 'koKR'
    Taiwanese = 'zhTW'


# for images
raw_asset_link_header='https://raw.githubusercontent.com/ScobraCK/MementoMori-data/main/Assets'

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
    512: 'LR'
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
    4: 'Socerer'
}

uw_rarity_skill_map = {
    128: "Description1Key",
    256: "Description2Key",
    512: "Description3Key"
}

uw_rarity_list = ['SSR', 'UR', 'LR']

class Skill_Enum(Enum):
    ACTIVE = 'Active Skills'
    PASSIVE = 'Passive Skills'

rarity_emoji = {
    'R': ':small_blue_diamond:',
    'SR': ':small_orange_diamond:',
    'SSR': '<:purple_diamond:1060066214723981394>',
    'UR': '<:red_diamond:1060066217257341048>',
    'LR': '<:black_diamond:1060067332589899866>'
}
level_emoji = {
    1: ':small_blue_diamond:',
    2: ':small_orange_diamond:',
    3: '<:purple_diamond:1060066214723981394>',
    4: '<:red_diamond:1060066217257341048>', 
}

# limited events
event_type = {
    1: {
        'name': 'Tower Release Event',
        'description': 'For a limited time, all Souls in the Tower of Infinity will be unlocked!'}
}

# timezones (hours in timedelta)
class Timezone(Enum):
    NA = -7
    JP = 9
    KR = 9
    EU = 1
    ASIA = 8
    GLOBAL = 1

# notes
passive_skill_triggers = {
    0: 'not in battle',
    1: 'turn start',
    2: 'end turn',
    5: 'amleth immortal trigger',
    6: 'sonya , amour, rusalka (???)',
    7: 'ally defeated',
    8: 'attacked + after damage / self',
    9: 'attack and trigger on attacked side',
    10: 'ally attacked',
    11: 'debuff applied to self / self',
    19: 'death? (amour, rusalka)',
    21: 'target defeated',
    27: 'end of battle',
    28: 'Battle start (speed buffs)',
    29: 'carol, after ally attacked, I have no idea',
    42: 'attacked + before damage / self',
}
'''
1, 6
"Sonya lets out a Viking’s cry of triumph. 
At the start of the battle, this skill increases all allies’ ATK by 2%. 
A target’s ATK is further increased by 2% for each ally other than Sonya who is alive.",
    

6, 19  (also rusalka)
"enUS": "Until Amour finds her happy ending, 
she won’t let this fairy tale come to an close. 
If she is defeated, this skill revives Amour and restores HP equal to 30% of her max HP to her. 
She doesn’t let anyone who defiles her story get away, 
and also deals 1 direct attack equal to 10% of the total damage taken by her over the past 20 turns to the enemy directly in front of her. 
If Amour is defeated by an effect from a debuff, this skill does not activate. 
This skill activates only 1 time per battle.",

+19
"The targets of this skill become the enemy directly in front of Amour and 1 enemy adjacent to that target.",
        
amour max hp passive also triggers with 19 (death?)        
'''

# Thought this could be useful, not really needed

# class Skill_Level(TypedDict):
#     'Lv': int
#     'Description': str
#     'UW': str

# class Skill(TypedDict):
#     'Name': str
#     'Cooldown': int
#     'Descriptions': List[Skill_Level]
