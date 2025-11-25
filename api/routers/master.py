from fastapi import APIRouter, Request

from common import routes
from common.schemas import APIResponse
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    routes.MASTER_PATH,
    summary='MasterData',
    description='Returns masterdata json',
    response_model=APIResponse[list[dict]]
)
async def master(
    request: Request,
    mb: str):
    md: MasterData = request.app.state.md
    data = await md.get_MB(mb)
    return APIResponse[list[dict]].create(request, data)
