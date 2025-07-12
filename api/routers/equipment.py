from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.string_keys import translate_keys
from api.schemas import requests
from api.schemas.equipment import get_equipment, get_upgrade_costs
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/equipment/search',
    summary='Equipment Search',
    description='Search equipment info.',
    response_model=schemas.APIResponse[schemas.Equipment]
)
async def search_equipment(
    session: SessionDep,
    request: Request,
    payload: requests.EquipmentRequest = Depends(),
    language: Language = Depends(language_parameter)
 ):
    md: MasterData = request.app.state.md
    eq = await get_equipment(md, payload)
    await translate_keys(eq, session, language)
    return schemas.APIResponse[schemas.Equipment].create(request, eq)

@router.get(
    '/equipment/unique/search',
    summary='Unique Equipment Search',
    description='Search unique equipment info.',
    response_model=schemas.APIResponse[schemas.UniqueWeapon],
)
async def search_uw(
    session: SessionDep,
    request: Request,
    payload: requests.UniqueWeaponRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    eq = await get_equipment(md, payload)
    await translate_keys(eq, session, language)
    return schemas.APIResponse[schemas.UniqueWeapon].create(request, eq)

@router.get(
    '/equipment/upgrade',
    summary='Equipment Upgrade Costs',
    description='Get upgrade costs for schemas. Use /equipment/search or equipment/unique/search for equip_id.',
    response_model=schemas.APIResponse[schemas.EquipmentCosts]
)
async def upgrade_cost(
    session: SessionDep,
    request: Request,
    payload: requests.EquipmentCostRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    costs = await get_upgrade_costs(md, payload)
    await translate_keys(costs, session, language)
    return schemas.APIResponse[schemas.EquipmentCosts].create(request, costs)

@router.get(
    '/equipment/{eqp_id}',
    summary='Equipment',
    description='Get equipment info.',
    response_model=schemas.APIResponse[schemas.Equipment]|schemas.APIResponse[schemas.UniqueWeapon]
)
async def equipment(
    session: SessionDep,
    request: Request,
    eqp_id: int,
    language: Language = Depends(language_parameter)
):
    '''Direct equipment id query'''
    md: MasterData = request.app.state.md
    eq_schema = await get_equipment(md, eqp_id)
    await translate_keys(eq_schema, session, language)

    if isinstance(eq_schema, schemas.UniqueWeapon):
        return schemas.APIResponse[schemas.UniqueWeapon].create(request, eq_schema)
    return schemas.APIResponse[schemas.Equipment].create(request, eq_schema)
