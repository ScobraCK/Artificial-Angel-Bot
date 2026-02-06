from api.utils.masterdata import MasterData
from api.utils.error import APIError
from api.schemas.equipment import search_uw_info
from api.schemas.string_keys import get_uw_desc_strings
from common import schemas

async def find_character_skill_ids(md: MasterData, id: int) -> tuple[list[int], list[int]]:
    char_data = await md.search_id(id, 'CharacterMB')
    if not char_data:
        raise APIError(f'Could not find character id {id}')

    return char_data.get('ActiveSkillIds'), char_data.get('PassiveSkillIds')

async def find_uw_descriptions(md: MasterData, character: int) -> schemas.UWDescriptions|None:
    eq_data = await search_uw_info(md, character)
    if not eq_data:
        return None
    desc_id = eq_data.get('EquipmentExclusiveSkillDescriptionId')
    if desc_id == 0:
        return None
    uw_desc = await md.search_id(desc_id, 'EquipmentExclusiveSkillDescriptionMB')
    return schemas.UWDescriptions(**uw_desc)

async def parse_skill(md: MasterData, id: int) -> schemas.ActiveSkill|schemas.PassiveSkill:
    skill_data = await md.search_id(id, 'ActiveSkillMB')
    if skill_data:  # Active
        return schemas.ActiveSkill(**skill_data)
    else:  # Check Passive
        skill_data = await md.search_id(id, 'PassiveSkillMB')
        if skill_data: # Not found
            return schemas.PassiveSkill(**skill_data)
    raise APIError(f'Could not find skill id of {id}')

async def get_skill_id(md: MasterData, skill_id: int) -> schemas.ActiveSkill|schemas.PassiveSkill:
    return await parse_skill(md, skill_id)

async def get_skills_char(md: MasterData, char_id: int) -> schemas.Skills:
    active_ids, passives_ids = await find_character_skill_ids(md, char_id)
    actives = []
    passives = []
    for id in active_ids:
        actives.append(await parse_skill(md, id))
    for id in passives_ids:
        passives.append(await parse_skill(md, id))

    uw_desc = await find_uw_descriptions(md, char_id)

    return schemas.Skills(
        character=char_id,
        actives=actives,
        passives=passives,
        uw_descriptions=uw_desc
    )
        