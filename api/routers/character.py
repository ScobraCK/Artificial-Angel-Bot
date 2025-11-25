from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse

from api.crud.character import get_filtered_chars, find_alts, get_all_alts
from api.crud.string_keys import translate_keys
from api.schemas.requests import CharacterDBRequest
from common.schemas import APIResponse
from api.schemas.character import (
    get_character, get_profile, get_lament, get_voicelines, get_memories, get_arcana
)
from api.schemas.requests import ArcanaRequest
from api.schemas.skills import get_skills_char
from api.utils.deps import SessionDep, language_parameter
from api.utils.error import APIError
from api.utils.masterdata import MasterData
from common import schemas, routes
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    routes.CHARACTER_SEARCH_PATH,
    summary='Simple character info filter',
    description='Returns a list of simple character data. See "option" query for provided data and filter options',
    response_model=APIResponse[list[schemas.CharacterDBModel]]
)
async def character_list(
    session: SessionDep,
    request: Request,
    payload: CharacterDBRequest = Depends()
    ):
    filtered = await get_filtered_chars(session, payload.option, value=payload.value, minvalue=payload.minvalue, maxvalue=payload.maxvalue)
    return APIResponse[list[schemas.CharacterDBModel]].create(request, filtered)

@router.get(
    routes.CHARACTER_INFO_PATH,
    summary='Basic character data',
    description='Returns basic character information',
    response_model=APIResponse[schemas.Character]
)
async def character(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    char = await get_character(md, char_id)
    await translate_keys(char, session, language)
    return APIResponse[schemas.Character].create(request, char)

@router.get(
    routes.CHARACTER_PROFILE_PATH,
    summary='Character profile data',
    description='Returns profile information',
    response_model=APIResponse[schemas.Profile]
)
async def profile(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    profile = await get_profile(md, char_id)
    await translate_keys(profile, session, language)
    return APIResponse[schemas.Profile].create(request, profile)

@router.get(
    routes.CHARACTER_LAMENT_PATH,
    summary='Character lament data',
    description='Returns lament information',
    response_model=APIResponse[schemas.Lament]
)
async def lament(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    lament = await get_lament(md, char_id)
    await translate_keys(lament, session, language)
    return APIResponse[schemas.Lament].create(request, lament)

@router.get(
    routes.CHARACTER_SKILL_PATH,
    summary='Character skill data',
    description='Returns character skill information',
    response_model=APIResponse[schemas.Skills]
)
async def skill(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    skills = await get_skills_char(md, char_id)
    await translate_keys(skills, session, language)
    return APIResponse[schemas.Skills].create(request, skills)

@router.get(
    routes.CHARACTER_VOICE_PATH,
    summary='Character voiceline data',
    description='Returns character voiceline information. Since original data is intended for ingame voiceline UI this does not include gacha voicelines and battle start voiceline.',
    response_model=APIResponse[schemas.CharacterVoicelines]
)
async def voiceline(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    voicelines = await get_voicelines(md, char_id)
    await translate_keys(voicelines, session, language)
    return APIResponse[schemas.CharacterVoicelines].create(request, voicelines)

@router.get(
    routes.CHARACTER_MEMORY_PATH,
    summary='Character memory data',
    description='Returns character memory information.',
    response_model=APIResponse[schemas.CharacterMemories]
)
async def memory(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    memories = await get_memories(md, char_id)
    await translate_keys(memories, session, language)
    return APIResponse[schemas.CharacterMemories].create(request, memories)

@router.get(
    routes.CHARACTER_ALTS_PATH,
    summary='All alt character ID mapping',
    description='Returns dict of {Base Character ID: [Alt Character IDs]} for all characters. Includes base character in alt ids.',
    response_model=APIResponse[dict[int, list[int]]]
)
async def all_alts(
    session: SessionDep,
    request: Request,
):
    alts = await get_all_alts(session)
    return APIResponse[dict[int, list[int]]].create(request, alts)

@router.get(
    routes.CHARACTER_ALTS_ID_PATH,
    summary='Find base and alt character ids',
    description='Returns dict of {Base Character ID: [Alt Character IDs]} for the given character. Includes base character in alt ids.',
    response_model=APIResponse[dict[int, list[int]]]
)
async def alts_by_id(
    session: SessionDep,
    request: Request,
    char_id: int,
):
    alts = await find_alts(session, char_id)
    return APIResponse[dict[int, list[int]]].create(request, alts)

@router.get(
    routes.ARCANA_PATH,
    summary='Arcana data',
    description='Returns arcana data. Can filter by character, parameter category, type and change type.',
    response_model=APIResponse[list[schemas.Arcana]]
)
async def arcana(
    session: SessionDep,
    request: Request,
    payload: ArcanaRequest = Depends(),
    language: Language = Depends(language_parameter),

):
    md: MasterData = request.app.state.md
    arcana_data = await get_arcana(
        md,
        character=payload.character,
        parameter_category=payload.param_category,
        parameter_type=payload.param_type,
        parameter_change_type=payload.param_change_type,
        has_level_bonus=payload.level_bonus
    )
    
    if not arcana_data:
        raise HTTPException(status_code=404, detail='No arcana data found with the provided filter conditions')
    await translate_keys(arcana_data, session, language)

    return APIResponse[list[schemas.Arcana]].create(request, arcana_data)

@router.get(
    routes.CHARACTER_ARCANA_PATH,
    summary='Arcana data by character ID',
    description=f'Same as {routes.ARCANA_PATH} with character specified.',
    response_model=APIResponse[list[schemas.Arcana]]
)
async def character_arcana(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter),

):
    md: MasterData = request.app.state.md
    arcana_data = await get_arcana(md, character=char_id)
    
    if not arcana_data:
        raise HTTPException(status_code=404, detail=f'No arcana data found for character {char_id}')
    await translate_keys(arcana_data, session, language)

    return APIResponse[list[schemas.Arcana]].create(request, arcana_data)

# Redirects for old routes
@router.get('/character/list', include_in_schema=False)
async def redirect_character_search():
    return RedirectResponse(url=routes.CHARACTER_SEARCH_PATH)

@router.get('/character/{char_id}', include_in_schema=False)
async def redirect_character_info(char_id: int):
    return RedirectResponse(url=routes.CHARACTER_INFO_PATH.format(char_id=char_id))

@router.get('/character/{char_id}/profile', include_in_schema=False)
async def redirect_character_profile(char_id: int):
    return RedirectResponse(url=routes.CHARACTER_PROFILE_PATH.format(char_id=char_id))

@router.get('/character/{char_id}/lament', include_in_schema=False)
async def redirect_character_lament(char_id: int):
    return RedirectResponse(url=routes.CHARACTER_LAMENT_PATH.format(char_id=char_id))

@router.get('/character/{char_id}/skill', include_in_schema=False)
async def redirect_character_skill(char_id: int):
    return RedirectResponse(url=routes.CHARACTER_SKILL_PATH.format(char_id=char_id))

@router.get('/character/{char_id}/voiceline', include_in_schema=False)
async def redirect_character_voice(char_id: int):
    return RedirectResponse(url=routes.CHARACTER_VOICE_PATH.format(char_id=char_id))

@router.get('/character/{char_id}/memory', include_in_schema=False)
async def redirect_character_memory(char_id: int):
    return RedirectResponse(url=routes.CHARACTER_MEMORY_PATH.format(char_id=char_id))

@router.get('/arcana', include_in_schema=False)
async def redirect_arcana_search():
    return RedirectResponse(url=routes.ARCANA_PATH)