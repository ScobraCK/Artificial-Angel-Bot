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
