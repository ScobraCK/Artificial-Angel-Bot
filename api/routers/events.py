from fastapi import APIRouter, Request, Depends
from typing import List

from common.schemas import APIResponse
from api.schemas.events import get_gacha
from api.schemas.requests import GachaRequest
from api.utils.masterdata import MasterData
from common import schemas

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/gacha',
    summary='Gacha Banner Info',
    description='Returns gacha banner information',
    response_model=APIResponse[List[schemas.GachaPickup]]
)
async def filtered_req(
    request: Request,
    payload: GachaRequest = Depends()
    ):
    md: MasterData = request.app.state.md
    gacha = await get_gacha(md, payload.char_id, payload.is_active)
    return APIResponse[List[schemas.GachaPickup]].create(request, gacha)