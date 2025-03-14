from fastapi import APIRouter, HTTPException, Request, Depends

import api.schemas.pve as pve
from api.schemas.api_models import APIResponse
from api.utils.deps import SessionDep, language_parameter
from api.utils.enums import Language
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/quest/{quest_id}',
    summary='Quest search',
    description='Returns main quest data',
    response_model=APIResponse[pve.Quest]
)
async def quest_req(
    session: SessionDep,
    request: Request,
    quest_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    quest = await pve.get_quest(md, quest_id)
    return APIResponse[pve.Quest].create(request, quest.model_dump(context={'db': session, 'language': language}))

@router.get(
    '/tower',
    summary='tower search',
    description='Returns tower data',
    response_model=APIResponse[pve.Tower]
)
async def tower_req(
    session: SessionDep,
    request: Request,
    payload: pve.TowerRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tower = await pve.get_tower(md, payload)
    return APIResponse[pve.Tower].create(request, tower.model_dump(context={'db': session, 'language': language}))
