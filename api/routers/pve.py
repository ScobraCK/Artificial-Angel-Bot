from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.string_keys import translate_keys
from api.schemas.pve import get_quest, get_tower
from api.schemas.requests import TowerRequest
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/quest/{quest_id}',
    summary='Quest search',
    description='Returns main quest data',
    response_model=schemas.APIResponse[schemas.Quest]
)
async def quest(
    session: SessionDep,
    request: Request,
    quest_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    quest = await get_quest(md, quest_id)
    await translate_keys(quest, session, language)
    return schemas.APIResponse[schemas.Quest].create(request, quest)

@router.get(
    '/tower',
    summary='tower search',
    description='Returns tower data',
    response_model=schemas.APIResponse[schemas.Tower]
)
async def tower(
    session: SessionDep,
    request: Request,
    payload: TowerRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tower = await get_tower(md, payload)
    await translate_keys(tower, session, language)
    return schemas.APIResponse[schemas.Tower].create(request, tower)
