from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.character import get_filtered_chars
from api.crud.string_keys import translate_keys
from api.schemas.requests import CharacterDBRequest
from common.schemas import APIResponse
from api.schemas.character import (
    get_character, get_profile, get_lament, get_voicelines, get_memories
)
from api.schemas.skills import get_skills_char
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/character/list',
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
    '/character/{char_id}',
    summary='Character lament data',
    description='Returns lament information',
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
    '/character/{char_id}/profile',
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
    '/character/{char_id}/lament',
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
    '/character/{char_id}/skill',
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
    # Prevents pve only character skill text showing up in bot
    check = await md.search_id(char_id, 'CharacterProfileMB')
    if check is None:
        raise HTTPException(status_code=404, detail=f'Could not find character id {char_id}')
    skills = await get_skills_char(md, char_id)
    await translate_keys(skills, session, language)
    return APIResponse[schemas.Skills].create(request, skills)

@router.get(
    '/character/{char_id}/voiceline',
    summary='Character voiceline data',
    description='Returns character voiceline information. Original data intended for voiceline animations. Does not include gacha voicelines and battle start voiceline.',
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
    '/character/{char_id}/memory',
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
