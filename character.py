from master_data import MasterData
import common
import equipment
from fuzzywuzzy import process, fuzz
from typing import Iterable, Literal, Optional

def get_character_info(
    id: int, master: MasterData, lang: Optional[common.Language]='enUS') -> dict:
    
    char_data = master.search_id(id, 'CharacterMB')
    char = {}  # to be changed to class

    char['Id'] = char_data['Id']
    char['Title'] = master.search_string_key(char_data['Name2Key'], language=lang)
    char['Name'] = master.search_string_key(char_data['NameKey'], language=lang)
    char['Element'] = common.souls[char_data['ElementType']]
    char['Base Rarity'] = common.char_rarity[char_data['RarityFlags']]
    char['Class'] = common.job_map[char_data['JobFlags']]
    char['Base Speed'] = char_data['InitialBattleParameter']['Speed']
    char['Normal Attack'] = common.normal_skills[char_data["NormalSkillId"]]
    char['UW'] = equipment.get_uw_name(id, master, lang=lang)

    char['Active Skills'] = char_data["ActiveSkillIds"]
    char["Passive Skills"] = char_data["PassiveSkillIds"]

    return char


def find_id_from_name(char_str: str):
    '''
    uses fuzzy matching to find id from a string. Uses a separate dictionary for speed.
    '''
    if (char:=char_str.lower()) in common.char_list:
        id = common.char_list[char]
    else:
        chars = common.char_list.keys()
        char,_ = process.extractOne(char_str, chars, scorer=fuzz.partial_ratio)
        id = common.char_list[char]

    return id

def check_id(id: int) -> bool:
    '''
    Returns if an id is a valid id
    '''
    if 1 <= id <= common.MAX_CHAR_ID:
        return True
    else:
        return False

def get_name(id: int, master: MasterData, lang: Optional[common.Language]='enUS'):
    char = master.search_id(id, 'CharacterMB')
    name = master.search_string_key(char.get('NameKey'), language=lang)
    return name

def speed_iter(masterdata: MasterData) -> Iterable:
    '''
    returns an iterable with character speeds in decreasing order
    Element is a tuple of (id, speed)
    '''

    char_speed = {x['Id']: x['InitialBattleParameter']['Speed'] for x in masterdata.get_chardata()}
    sorted_char = sorted(
        char_speed.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return iter(sorted_char)

# testing
if __name__ == "__main__":
    master = MasterData()
    print(get_name(find_id_from_name('ーリン'), master))
    