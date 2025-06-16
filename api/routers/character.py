from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

from api.crud.character import get_filtered_chars
from api.schemas.requests import CharacterDBRequest
from common.schemas import APIResponse
from api.schemas.character import (
    get_character, get_profile, get_lament, get_voicelines, get_memories
)
from api.schemas.skills import get_skills_char
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from api.utils.transformer import Transformer
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/character/list',
    summary='Simple character info filter',
    description='Returns a list of simple character data. See "option" query for provided data and filter options',
    response_model=APIResponse[List[schemas.CharacterDBModel]]
)
async def filtered_req(
    session: SessionDep,
    request: Request,
    payload: CharacterDBRequest = Depends()
    ):
    filtered = await get_filtered_chars(session, payload.option, value=payload.value, minvalue=payload.minvalue, maxvalue=payload.maxvalue)
    return APIResponse[List[schemas.CharacterDBModel]].create(request, filtered)

@router.get(
    '/character/{char_id}',
    summary='Character lament data',
    description='Returns lament information',
    response_model=APIResponse[schemas.Character]
)
async def char_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    char = await tf.transform(await get_character(md, char_id))
    return APIResponse[schemas.Character].create(request, char)

@router.get(
    '/character/{char_id}/profile',
    summary='Character profile data',
    description='Returns profile information',
    response_model=APIResponse[schemas.Profile]
)
async def profile_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    profile = await tf.transform(await get_profile(md, char_id))
    return APIResponse[schemas.Profile].create(request, profile)

@router.get(
    '/character/{char_id}/lament',
    summary='Character lament data',
    description='Returns lament information',
    response_model=APIResponse[schemas.Lament]
)
async def lament_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    lament = await tf.transform(await get_lament(md, char_id))
    return APIResponse[schemas.Lament].create(request, lament)

@router.get(
    '/character/{char_id}/skill',
    summary='Character skill data',
    description='Returns character skill information',
    response_model=APIResponse[schemas.Skills]
)
async def skill_req(
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
    tf = Transformer(session, language)
    skills = await tf.transform(await get_skills_char(md, char_id))
    return APIResponse[schemas.Skills].create(request, skills)

@router.get(
    '/character/{char_id}/voiceline',
    summary='Character voiceline data',
    description='Returns character voiceline information. Original data intended for voiceline animations. Does not include gacha voicelines and battle start voiceline.',
    response_model=APIResponse[schemas.CharacterVoicelines]
)
async def voiceline_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    voicelines = await tf.transform(await get_voicelines(md, char_id))
    return APIResponse[schemas.CharacterVoicelines].create(request, voicelines)

@router.get(
    '/character/{char_id}/memory',
    summary='Character memory data',
    description='Returns character memory information.',
    response_model=APIResponse[schemas.CharacterMemories]
)
async def memory_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    memories = await tf.transform(await get_memories(md, char_id))
    return APIResponse[schemas.CharacterMemories].create(request, memories)
