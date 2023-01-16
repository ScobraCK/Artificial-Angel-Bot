'''
Character skills
'''

from master_data import MasterData
from typing import Literal, Optional
from common import Skill_Enum


def skill_info(
    char: dict,
    type: Skill_Enum,
    descriptions: bool=True,
    masterdata: MasterData=None,
    lang: Optional[Literal['enUS', 'jaJP', 'koKR', 'zhTW']]='enUS'):
    '''
    returns skill data
    give either skill_id or char_id to search
    type: Active or Passive
    descriptions: Only returns name and cooldown if False

    If no passive an empty list is returned
    '''

    if masterdata is None:
        masterdata = MasterData()

    if type is Skill_Enum.ACTIVE:
        skill_info_key = 'ActiveSkillInfos'
        search_skill = masterdata.search_active_skill
    else:
        skill_info_key = 'PassiveSkillInfos'
        search_skill = masterdata.search_passive_skill

    skill_ids = char[type.value]
    skills = []

    for id in skill_ids:
        skill = {}
        skill_data = search_skill(id)
        
        skill['Name'] = masterdata.search_string_key(skill_data["NameKey"], language=lang)
        skill['Cooldown'] = skill_data.get('SkillMaxCoolTime')  # only useful for actives currently
        # SkillInitCoolTime (is this used?)
        
        if descriptions:
            skill['Descriptions'] = []
            for level in skill_data[skill_info_key]:
                description = masterdata.search_string_key(level["DescriptionKey"], language=lang)
                if description:  # Unknown cases (Flor S1m Mimi S2 etc as of 2023/01/02)
                    if (level["EquipmentRarityFlags"] == 0):  # normal skill description
                        skill_level = {
                                'Lv': level["CharacterLevel"],
                                'Description': description
                            }
                        skill['Descriptions'].append(skill_level)
                # else:  # testing for wierd skills
                #     print(char_id)
        
        skills.append(skill)
    return skills


#testing
if __name__ == "__main__":
    from pprint import pprint
    master = MasterData()
