from master_data import MasterData
import common
import equipment
from fuzzywuzzy import process, fuzz
from typing import List, Iterable, Literal, Optional

def get_character_info(
    id: int, masterdata: MasterData=None, lang: Optional[Literal['enUS', 'jaJP', 'koKR', 'zhTW']]='enUS') -> dict:
    if masterdata is None:
        masterdata = MasterData()
    char_data = next(masterdata.search_chars(id=id))
    char = {}

    char['Id'] = char_data['Id']
    char['Title'] = masterdata.search_string_key(char_data['Name2Key'], language=lang)
    char['Name'] = masterdata.search_string_key(char_data['NameKey'], language=lang)
    char['Element'] = common.souls[char_data['ElementType']]
    char['Base Rarity'] = common.char_rarity[char_data['RarityFlags']]
    char['Class'] = common.job_map[char_data['JobFlags']]
    char['Base Speed'] = char_data['InitialBattleParameter']['Speed']
    char['Normal Attack'] = common.normal_skills[char_data["NormalSkillId"]]
    char['UW'] = equipment.get_uw_name(id, masterdata, lang=lang)

    char['Active Skills'] = char_data["ActiveSkillIds"]
    char["Passive Skills"] = char_data["PassiveSkillIds"]

    return char


def find_id_from_name(char_str: str):
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

def get_name(id: int, master: MasterData, lang='enUS'):
    char = next(master.search_chars(id=id))
    name = master.search_string_key(char.get('NameKey'), language=lang)
    return name

def speed_iter(masterdata: MasterData) -> Iterable:
    '''
    returns an iterable with character speeds in decreasing order
    Element is a tuple of (id, speed)
    '''
    if masterdata is None:
        masterdata = MasterData()
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
    print(get_name(12, master))
    