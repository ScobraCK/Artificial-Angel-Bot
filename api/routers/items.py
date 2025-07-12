from fastapi import APIRouter, Depends, Request

from api.crud.string_keys import translate_keys
from api.schemas.items import get_item, get_runes
from api.schemas.requests import ItemRequest
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from common import enums, schemas

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/item',
    summary='Item',
    description='Returns item data',
    response_model=schemas.APIResponse[schemas.Item]
)
async def item(
    session: SessionDep,
    request: Request,
    payload: ItemRequest = Depends(),
    language: enums.Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    item = await get_item(md, payload)
    await translate_keys(item, session, language)
    return schemas.APIResponse[schemas.Item].create(request, item)

@router.get(
    '/item/rune',
    summary='Rune',
    description='Returns all rune data',
    response_model=schemas.APIResponse[list[schemas.Rune]]
)
async def rune(
    session: SessionDep,
    request: Request,
    language: enums.Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    runes = await get_runes(md)
    await translate_keys(runes, session, language)
    return schemas.APIResponse[list[schemas.Rune]].create(request, runes)

@router.get(
    '/item/rune/{category}',
    summary='Rune Category',
    description=(
        'Returns rune data for rune types(category)<br>'
        '1-STR<br>'
        '2-DEX<br>'
        '3-MAG<br>'
        '4-ATK<br>'
        '5-PM.DEF Break<br>'
        '6-ACC<br>'
        '7-CRIT<br>'
        '8-Debuff ACC<br>'
        '9-SPD<br>'
        '10-STA<br>'
        '11-HP<br>'
        '12-P.DEF<br>'
        '13-M.DEF<br>'
        '14-EVD<br>'
        '15-CRIT RES<br>'
        '16-Debuff RES'
    ),
    response_model=schemas.APIResponse[list[schemas.Rune]]
)
async def rune_search(
    session: SessionDep,
    request: Request,
    category: enums.RuneType,
    language: enums.Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    runes = await get_runes(md, category)
    await translate_keys(runes, session, language)
    return schemas.APIResponse[list[schemas.Rune]].create(request, runes)
