from fastapi import APIRouter, HTTPException, Request, Depends

from common.schemas import APIResponse
from api.schemas.pve import get_quest, get_tower
from api.schemas.requests import TowerRequest
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from api.utils.transformer import Transformer
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/quest/{quest_id}',
    summary='Quest search',
    description='Returns main quest data',
    response_model=APIResponse[schemas.Quest]
)
async def quest_req(
    session: SessionDep,
    request: Request,
    quest_id: int,
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    quest = await tf.transform(await get_quest(md, quest_id))
    return APIResponse[schemas.Quest].create(request, quest)

@router.get(
    '/tower',
    summary='tower search',
    description='Returns tower data',
    response_model=APIResponse[schemas.Tower]
)
async def tower_req(
    session: SessionDep,
    request: Request,
    payload: TowerRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    tower = await tf.transform(await get_tower(md, payload))
    return APIResponse[schemas.Tower].create(request, tower)
