from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

from common.schemas import APIResponse
from api.schemas.items import get_item
from api.schemas.requests import ItemRequest
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from api.utils.transformer import Transformer
from common.schemas import Item
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/item',
    summary='Item',
    description='Returns item data',
    response_model=APIResponse[Item]
)
async def item_req(
    session: SessionDep,
    request: Request,
    payload: ItemRequest = Depends(),
    language: Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    item = await tf.transform(await get_item(md, payload))
    return APIResponse[Item].create(request, item)
