from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Union

from api.schemas import requests
from common.schemas import APIResponse
from api.schemas.equipment import get_equipment, get_upgrade_costs
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from api.utils.transformer import Transformer
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/equipment/search',
    summary='Equipment Search',
    description='Search equipment info.',
    response_model=APIResponse[schemas.Equipment]
)
async def search_equipment_req(
    session: SessionDep,
    request: Request,
    payload: requests.EquipmentRequest = Depends(),
    language: Language = Depends(language_parameter)
 ):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    eq = await tf.transform(await get_equipment(md, payload))
    return APIResponse[schemas.Equipment].create(request, eq)

@router.get(
    '/equipment/unique/search',
    summary='Unique Equipment Search',
    description='Search unique equipment info.',
    response_model=APIResponse[schemas.UniqueWeapon],
)
async def search_uw_req(
    session: SessionDep,
    request: Request,
    payload: requests.UniqueWeaponRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    eq = await tf.transform(await get_equipment(md, payload))
    return APIResponse[schemas.UniqueWeapon].create(request, eq)

@router.get(
    '/equipment/upgrade',
    summary='Equipment Upgrade Costs',
    description='Get upgrade costs for schemas. Use /equipment/search or equipment/unique/search for equip_id.',
    response_model=APIResponse[schemas.EquipmentCosts]
)
async def upgrade_cost_req(
    session: SessionDep,
    request: Request,
    payload: requests.EquipmentCostRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    costs = await tf.transform(await get_upgrade_costs(md, payload))
    return APIResponse[schemas.EquipmentCosts].create(request, costs)

@router.get(
    '/equipment/{eqp_id}',
    summary='Equipment',
    description='Get equipment info.',
    response_model=Union[APIResponse[schemas.Equipment],APIResponse[schemas.UniqueWeapon]]
)
async def equipment_req(
    session: SessionDep,
    request: Request,
    eqp_id: int,
    language: Language = Depends(language_parameter)
):
    '''Direct equipment id query'''
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    eq_schema = await get_equipment(md, eqp_id)

    if isinstance(eq_schema, schemas.UniqueWeapon):
        return APIResponse[schemas.UniqueWeapon].create(request, await tf.transform(eq_schema))
    return APIResponse[schemas.Equipment].create(request, await tf.transform(eq_schema))
