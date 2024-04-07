'''
Character skills
'''

from master_data import MasterData
from typing import List, Literal, Optional, Union
from common import Skill_Enum, Language, equip_rarity
from equipment import get_uw_descriptions
import emoji

def skill_info(
    char: dict,
    type: Skill_Enum,
    master: MasterData,
    descriptions: bool=True,
    lang: Optional[Language]='enUS'):
    '''
    returns skill data

    type: Active or Passive
    descriptions: Only returns name and cooldown if False

    If the character has no passive an empty list is returned
    '''

    if type is Skill_Enum.Active:
        skill_type = 'Active Skills'
        skill_info_type = 'ActiveSkillInfos'
        skill_MB = 'ActiveSkillMB'
    else:
        skill_type = 'Passive Skills'
        skill_info_type = 'PassiveSkillInfos'
        skill_MB = 'PassiveSkillMB'

    skill_ids = char[skill_type]
    skills = []

    for id in skill_ids:
        skill = {}
        skill_data = master.search_id(id, skill_MB)
        
        skill['Name'] = master.search_string_key(skill_data["NameKey"], language=lang)
        skill['Cooldown'] = skill_data.get('SkillMaxCoolTime')
        
        if descriptions:
            skill['Descriptions'] = []
            for level in skill_data[skill_info_type]:
                description = master.search_string_key(level["DescriptionKey"], language=lang)
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

class Subskill():
    def __init__(
            self, 
            skill_level:int, unlock_level: int, description: str,
            subsetskills: List[Union[int, dict]], uw_rarity:str=None) -> None:
        self.skill_level = skill_level
        self.unlock_level = unlock_level
        self.description = description
        self.subsetskills = subsetskills  # int for active, dict for passives
        self.uw_rarity = uw_rarity
        self.emoji = None # discord emoji for skill level

class Skill():
    def __init__(self, 
                name: str, skill_id: int, type: Skill_Enum, type_name: str,
                subskills: List[Subskill]) -> None:
        self.name = name
        self.skill_id = skill_id
        self.type = type
        self.type_name = type_name
        self.icon = f"CSK_00{skill_id:07}.png"
        self.subskills = subskills

class ActiveSkill(Skill):
    def __init__(self, name: str, skill_id: int, type: Skill_Enum, type_name: str, 
                 subskills: List[Subskill], max_cd: int, init_cd: int) -> None:
        super().__init__(name, skill_id, type, type_name, subskills)
        self.max_cd = max_cd
        self.init_cd = init_cd

class PassiveSkill(Skill):
    def __init__(self, name: str, skill_id: int, type: Skill_Enum, 
                 type_name: str, subskills: List[Subskill]) -> None:
        super().__init__(name, skill_id, type, type_name, subskills)


def get_subskill(
        subskill_data: dict, type: Skill_Enum, skill_level:int, 
        uw_desc:dict, master: MasterData, lang: Optional[Language]='enUS'):

    unlock_lv = subskill_data["CharacterLevel"]
    # blessing = subskill_data['BlessingItemId']

    if type is Skill_Enum.Active:
        subsetskills = subskill_data['SubSetSkillIds']
    else:
        subsetskills = subskill_data['PassiveSubSetSkillInfos']

    if ((rarity := subskill_data["EquipmentRarityFlags"]) == 0):  # normal skill description
        description = master.search_string_key(subskill_data["DescriptionKey"], language=lang)
        subskill = Subskill(skill_level, unlock_lv, description, subsetskills)
    else:
        uw_rarity = equip_rarity.get(rarity)
        description = uw_desc.get(uw_rarity)
        subskill = Subskill(skill_level, unlock_lv, description, subsetskills, uw_rarity)
        subskill.emoji = emoji.rarity_emoji.get(uw_rarity)  # emoji is decided with UW level
    return subskill

def get_skill(
        skill_id: int, 
        type: Skill_Enum,
        uw_desc: dict,
        master:MasterData,
        lang: Optional[Language]='enUS'):
    
    if type is Skill_Enum.Active:
        skill_type = 'ActiveSkillInfos'
        skill_MB = 'ActiveSkillMB'
    else:
        skill_type = 'PassiveSkillInfos'
        skill_MB = 'PassiveSkillMB'

    skill_data = master.search_id(skill_id, skill_MB)    
    name = master.search_string_key(skill_data["NameKey"], language=lang)
    if name is None:
            name = 'Unnamed Skill'
    type_name = master.search_string_key(type.value)

    subskills = []
    for level in skill_data[skill_type]:
        skill_level = level.get('OrderNumber')
        subskill = get_subskill(level, type, skill_level,uw_desc, master, lang)
        if not subskill.emoji: # Skill is not UW weapon and has level       
            subskill.emoji = emoji.level_emoji.get(skill_level)
        subskills.append(subskill)

    if type is Skill_Enum.Active:
        max_cd = skill_data.get('SkillMaxCoolTime')
        init_cd = skill_data.get('SkillInitCoolTime')
        skill = ActiveSkill(name, skill_id, type, type_name, subskills, max_cd, init_cd)
    else:
        skill = PassiveSkill(name, skill_id, type, type_name, subskills)
    
    return skill

# new experimental skill
def skill_detail_info(
    char_id: int,
    master: MasterData,
    lang: Optional[Language]='enUS')->List[Skill]:
    '''
    returns a list of all skills data inclucding UW
    '''
    char_data = master.search_id(char_id, 'CharacterMB')
    active_ids = char_data["ActiveSkillIds"]
    passive_ids = char_data['PassiveSkillIds']

    skills = []
    uw_desc = get_uw_descriptions(char_id, master, lang)

    for skill_id in active_ids:
        skill = get_skill(skill_id, Skill_Enum.Active, uw_desc, master, lang)
        skills.append(skill)
    for skill_id in passive_ids:
        skill = get_skill(skill_id, Skill_Enum.Passive, uw_desc, master, lang)
        skills.append(skill)
        
    return skills

#testing
if __name__ == "__main__":
    from pprint import pprint
    master = MasterData()
    for skill in skill_detail_info(8, master):
        pprint(skill.__dict__)
