from fastapi import APIRouter, Request
from typing import List

from api.schemas.api_models import APIResponse
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/raw/master/{mb}',
    summary='MasterData',
    description='Returns raw masterdata',
    response_model=APIResponse[List[dict]]
)
async def master_req(
    request: Request,
    mb: str):
    md: MasterData = request.app.state.md
    data = await md.get_MB(mb)
    return APIResponse[List[dict]].create(request, data)
