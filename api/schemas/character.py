from typing import Literal

from api.utils.error import APIError
from api.utils.masterdata import MasterData
from api.schemas.equipment import search_uw_info
from common import schemas, enums

async def get_character(md: MasterData, id: int):
    char_data = await md.search_id(id, 'CharacterMB')
    uw_data = await search_uw_info(md, id)
    uw = uw_data.get('NameKey') if uw_data else None
    if char_data is None:
        raise APIError(f'Could not find character info with id {id}')
    return schemas.Character(**char_data, uw=uw)

async def get_profile(md: MasterData, id: int):
    profile_data = await md.search_id(id, 'CharacterProfileMB')
    if profile_data is None:
        raise APIError(f'Could not find character profile with id {id}')
    return schemas.Profile(**profile_data)

async def get_lament(md: MasterData, id: int):
    profile_data = await md.search_id(id, 'CharacterProfileMB')
    if profile_data is None:
        raise APIError(f'Could not find lament info with id {id}')
    return schemas.Lament(**profile_data)

async def get_voicelines(md: MasterData, id: int):
    voicelines = list(await md.search_filter('CharacterDetailVoiceMB', CharacterId=id))
    if not voicelines:
        raise APIError(f'Could not find voiceline info with id {id}')
    return schemas.CharacterVoicelines(char_id=id, voicelines=voicelines)

async def get_memories(md: MasterData, id: int):
    memories = list(await md.search_filter('CharacterStoryMB', CharacterId=id))
    if not memories:
        raise APIError(f'Could not find memory info with id {id}')
    return schemas.CharacterMemories(char_id=id, memories=memories)

async def get_arcana_rewards(md: MasterData) -> dict[tuple[int, int], dict]:
    rewards = {}
    for reward in await md.get_MB('CharacterCollectionRewardMB'):
        level = reward['CollectionLevel']
        count = reward['CharacterCount']
        rewards[(level, count)] = reward['RewardItems']

    return rewards

async def get_arcana_levels(md: MasterData) -> dict[int, list[dict]]:
    levels = {}
    for level in await md.get_MB('CharacterCollectionLevelMB'):
        arcana_id = level['CollectionId']
        if arcana_id not in levels:
            levels[arcana_id] = []
        levels[arcana_id].append(level)
    return levels

def check_parameter(
    parameter: schemas.Parameter,
    category: enums.ParameterCategory|None,
    parameter_type: int|None,
    change_type: enums.ParameterChangeType|None
) -> bool:
    if category is not None and category != parameter.category:
        return False
    if parameter_type is not None and parameter_type != parameter.type:
        return False
    if change_type is not None and change_type != parameter.change_type:
        return False
    return True

async def get_arcana(
    md: MasterData,
    character: int|None=None,
    parameter_category: enums.ParameterCategory|None=None,
    parameter_type: int|None=None,
    parameter_change_type: enums.ParameterChangeType|None=None,
    has_level_bonus: bool|None=None
) -> list[schemas.Arcana]:
    arcanas = []
    arcana_data = await md.get_MB('CharacterCollectionMB')
    level_data = await get_arcana_levels(md)
    reward_data = await get_arcana_rewards(md)

    for arcana in arcana_data:  # reverse filter. Continues if any of the conditions are met.
        if character and character not in arcana['RequiredCharacterIds']:
            continue

        levels: list[schemas.ArcanaLevel] = []
        char_count = len(arcana['RequiredCharacterIds'])
        for level in level_data.get(arcana['Id'], []):
            levels.append(schemas.ArcanaLevel(
                **level,
                reward=reward_data.get((level['CollectionLevel'], char_count), [])
            ))

        if levels:
            if parameter_category is not None or parameter_type is not None or parameter_change_type is not None:
                if not any(check_parameter(param, parameter_category, parameter_type, parameter_change_type) for param in levels[-1].parameters):
                    continue

            if has_level_bonus is not None:
                if (levels[-1].level_bonus > 0) != has_level_bonus:  # Left True => has level bonus. If left != has_level_bonus fails check.
                    continue


        arcanas.append(schemas.Arcana(**arcana, levels=levels))
    return arcanas

async def get_potential(
    md: MasterData,
) -> schemas.CharacterPotential:
    potential_data = await md.get_MB('CharacterPotentialMB')
    coefficients_data = await md.get_MB('CharacterPotentialCoefficientMB')

    levels = {}
    for potential in potential_data:
        key = f"{potential['CharacterLevel']}.{potential['CharacterSubLevel']}"
        levels[key] = potential['TotalBaseParameter']

    coefficients = {1: {}, 2: {}, 8: {}}
    for coeff in coefficients_data:
        coefficients[coeff['InitialRarityFlags']][coeff['RarityFlags']] = coeff['RarityCoefficientInfo']

    return schemas.CharacterPotential(
        levels=levels,
        coefficients=coefficients
    )

