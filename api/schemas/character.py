from typing import Literal

from api.utils.error import APIError
from api.utils.masterdata import MasterData
from api.schemas.equipment import search_uw_info
from common import schemas

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

async def get_arcana(
    md: MasterData,
    character: int|None=None,
    parameter_category: Literal['Base', 'Battle']|None=None,
    parameter_type: int|None=None,
    parameter_change_type: int|None=None
):
    arcanas = []
    arcana_data = await md.get_MB('CharacterCollectionMB')
    level_data = await get_arcana_levels(md)
    reward_data = await get_arcana_rewards(md)

    for arcana in arcana_data:
        if character and character not in arcana['RequiredCharacterIds']:
            continue

        levels: list[schemas.ArcanaLevel] = []
        char_count = len(arcana['RequiredCharacterIds'])
        for level in level_data.get(arcana['Id'], []):
            levels.append(schemas.ArcanaLevel(
                **level,
                reward=reward_data.get((level['CollectionLevel'], char_count), [])
            ))

        if levels and (parameter_category or parameter_type or parameter_change_type):
            for param in levels[-1].parameters:  # check from max level arcana
                if parameter_category is not None and parameter_category != param.category:
                    continue
                if parameter_type is not None and parameter_type != param.type:
                    continue
                if parameter_change_type is not None and parameter_change_type != param.change_type:
                    continue

        arcanas.append(schemas.Arcana(**arcana, levels=levels))
    return arcanas
