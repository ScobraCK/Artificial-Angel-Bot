from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

import api.schemas.character as char_schema
from api.crud.character import get_filtered_chars, get_char_ids
from api.models.character import CharacterDBModel, CharacterDBRequest
from api.schemas.api_models import APIResponse
from api.schemas.skills import Skills, get_skills_char
from api.utils.enums import Language
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/character/list',
    summary='Simple character info filter',
    description='Returns a list of simple character data. See "option" query for provided data and filter options',
    response_model=APIResponse[List[CharacterDBModel]]
)
async def filtered_req(
    session: SessionDep,
    request: Request,
    payload: CharacterDBRequest = Depends()
    ):
    filtered = await get_filtered_chars(session, payload.option, value=payload.value, minvalue=payload.minvalue, maxvalue=payload.maxvalue)
    return APIResponse[List[CharacterDBModel]].create(request, filtered)

@router.get(
    '/character/{char_id}',
    summary='Character lament data',
    description='Returns lament information',
    response_model=APIResponse[char_schema.Character]
)
async def char_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    char = await char_schema.get_character(md, char_id)
    return APIResponse[char_schema.Character].create(request, char.model_dump(context={'db': session, 'language': language}))

@router.get(
    '/character/{char_id}/profile',
    summary='Character profile data',
    description='Returns profile information',
    response_model=APIResponse[char_schema.Profile]
)
async def profile_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    profile = await char_schema.get_profile(md, char_id)
    # nullable str conversion due to stella
    return APIResponse[char_schema.Profile].create(request, profile.model_dump(context={'db': session, 'language': language, 'nullable': True}))

@router.get(
    '/character/{char_id}/lament',
    summary='Character lament data',
    description='Returns lament information',
    response_model=APIResponse[char_schema.Lament]
)
async def lament_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    lament = await char_schema.get_lament(md, char_id)
    return APIResponse[char_schema.Lament].create(request, lament.model_dump(context={'db': session, 'language': language}))

@router.get(
    '/character/{char_id}/skill',
    summary='Character skill data',
    description='Returns character skill information',
    response_model=APIResponse[Skills]
)
async def skill_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    # Prevents pve only character skill text showing up in bot  (Reverted due to issues)
    md: MasterData = request.app.state.md
    check = await md.search_id(char_id, 'CharacterProfileMB')
    if check is None:
        raise HTTPException(status_code=404, detail=f'Could not find character id {char_id}')
    skills = await get_skills_char(md, char_id)
    return APIResponse[Skills].create(request, skills.model_dump(context={'db': session, 'language': language}))

@router.get(
    '/character/{char_id}/voiceline',
    summary='Character voiceline data',
    description='Returns character voiceline information. Original data intended for voiceline animations. Does not include gacha voicelines and battle start voiceline.',
    response_model=APIResponse[char_schema.CharacterVoicelines]
)
async def voiceline_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    voicelines = await char_schema.get_voicelines(md, char_id)
    return APIResponse[char_schema.CharacterVoicelines].create(request, voicelines.model_dump(context={'db': session, 'language': language}))

@router.get(
    '/character/{char_id}/memory',
    summary='Character memory data',
    description='Returns character memory information.',
    response_model=APIResponse[char_schema.CharacterMemories]
)
async def memory_req(
    session: SessionDep,
    request: Request,
    char_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    memories = await char_schema.get_memories(md, char_id)
    return APIResponse[char_schema.CharacterMemories].create(request, memories.model_dump(context={'db': session, 'language': language}))
