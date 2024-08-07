from fuzzywuzzy import process, fuzz
from typing import Iterable, Literal, Optional
from collections import namedtuple
import re

from master_data import MasterData
import common
from equipment import get_uw_name

def get_character_info(
    id: int, master: MasterData, lang: Optional[common.Language]='enUS') -> dict:
    
    char_data = master.search_id(id, 'CharacterMB')
    if not char_data:
        return None
    char = {}  # to be changed to class

    char['Id'] = char_data['Id']
    char['Title'] = master.search_string_key(char_data['Name2Key'], language=lang)
    char['Name'] = master.search_string_key(char_data['NameKey'], language=lang)
    char['Element'] = common.souls[char_data['ElementType']]
    char['Base Rarity'] = common.char_rarity[char_data['RarityFlags']]
    char['Class'] = common.job_map[char_data['JobFlags']]
    char['Base Speed'] = char_data['InitialBattleParameter']['Speed']
    char['Normal Attack'] = common.normal_skills[char_data["NormalSkillId"]]
    char['UW'] = get_uw_name(id, master, lang=lang)

    char['Active Skills'] = char_data["ActiveSkillIds"]
    char["Passive Skills"] = char_data["PassiveSkillIds"]

    return char


def find_id_from_name(char_str: str):
    '''
    uses fuzzy matching to find id from a string. Uses a separate dictionary for speed.
    '''
    char = re.sub('[^A-Za-z0-9]+', '', char_str).lower()
    if char in common.char_list:
        id = common.char_list[char]
    else:
        chars = common.char_list.keys()
        char,_ = process.extractOne(char_str, chars, scorer=fuzz.ratio)
        id = common.char_list[char]

    return id

def check_id(id: int) -> bool:
    '''
    Returns if an id is a valid id
    '''
    if id in common.id_list.keys():
        return True
    else:
        return False

def get_name(id: int, master: MasterData, lang: Optional[common.Language]='enUS'):
    char = master.search_id(id, 'CharacterMB')
    if char:
        name = master.search_string_key(char.get('NameKey'), language=lang)
    else:
        name = None
    return name

def get_full_name(id: int, master: MasterData, lang: Optional[common.Language]='enUS'):
    char = master.search_id(id, 'CharacterMB')
    if char:
        name = master.search_string_key(char.get('NameKey'), language=lang)
        title = master.search_string_key(char.get('Name2Key'), language=lang)
        if title:
            name = f'[{title}] {name}'
    else:
        name = None

    return name

def speed_sorted(masterdata: MasterData) -> dict:
    '''
    Returns a dictionary with character speeds in decreasing order.
    Key is the character id and value is the speed.
    '''

    char_speed = {x['Id']: x['InitialBattleParameter']['Speed'] for x in masterdata.get_chardata()}
    sorted_char = sorted(
        char_speed.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Create a dictionary from the sorted list of tuples (insertion order is maintained)
    sorted_dict = dict(sorted_char)
    
    return sorted_dict

# voiceline
def get_voicelines(id: int, md: MasterData, lang: Optional[common.Language]='enUS') -> dict:
    '''
    Get char voicelines
    Returns:
        Dict[button_name, subtitle]
            etc {'Home1': <voiceline>}
    '''
    voiceline_data = md.search_voiceline(id)
    voicelines = {}
    for voice_data in voiceline_data:
        button = md.search_string_key(voice_data['UnlockedVoiceButtonTextKey'], lang)
        subtitle = md.search_string_key(voice_data['SubtitleKey'], lang)
        if subtitle:
            voicelines[button] = subtitle
    
    return voicelines

# memories
def get_memories(id: int, md: MasterData, lang: Optional[common.Language]='enUS') -> dict:
    '''
    Get char memories
    Returns:
        Dict[
            episode: text(html)
        ]
    '''
    memory_data = md.search_memories(id)
    memories = {}
    for memory in memory_data:
        episode = md.search_string_key(memory['TitleKey'], lang)
        text = md.search_string_key(memory['TextKey'], lang)
        if text:
            memories[episode] = text
    
    return memories

# testing
if __name__ == "__main__":
    import html2text
    h=  html2text.HTML2Text()
    master = MasterData()
    id = 78
    for  k, v in get_memories(id, master).items():
        print(f'{k}: {h.handle(v)}')
        break
