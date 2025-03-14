from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

import api.schemas.items as item_schema
from api.schemas.api_models import APIResponse
from api.utils.enums import Language
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/item',
    summary='Item',
    description='Returns item data',
    response_model=APIResponse[item_schema.Item]
)
async def item_req(
    session: SessionDep,
    request: Request,
    payload: item_schema.ItemRequest = Depends(),
    language: Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    item = await item_schema.get_item(md, payload)
    return APIResponse[item_schema.Item].create(request, item.model_dump(context={'db': session, 'language': language}))
