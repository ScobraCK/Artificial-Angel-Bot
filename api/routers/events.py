from fastapi import APIRouter, Request, Depends
from typing import List

from api.schemas import events as event_schema
from api.schemas.api_models import APIResponse
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/gacha',
    summary='Gacha Banner Info',
    description='Returns gacha banner information',
    response_model=APIResponse[List[event_schema.GachaPickup]]
)
async def filtered_req(
    request: Request,
    payload: event_schema.GachaRequest = Depends()
    ):
    md: MasterData = request.app.state.md
    gacha = await event_schema.get_gacha(md, payload.char_id, payload.is_active)
    return APIResponse[List[event_schema.GachaPickup]].create(request, gacha)