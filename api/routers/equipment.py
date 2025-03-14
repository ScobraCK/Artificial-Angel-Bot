from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Union

import api.schemas.equipment as equipment
from api.schemas.api_models import APIResponse
from api.utils.deps import SessionDep, language_parameter
from api.utils.enums import Language
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/equipment/search',
    summary='Equipment Search',
    description='Search equipment info.',
    response_model=APIResponse[equipment.Equipment]
)
async def search_equipment_req(
    session: SessionDep,
    request: Request,
    payload: equipment.EquipmentRequest = Depends(),
    language: Language = Depends(language_parameter)
 ):
    md: MasterData = request.app.state.md
    eq = await equipment.get_equipment(md, payload)
    
    eq_resp = equipment.Equipment(**eq.model_dump(context={'language': language, 'db': session}, exclude_none=True))
    return APIResponse[equipment.Equipment].create(request, eq_resp)

@router.get(
    '/equipment/unique/search',
    summary='Unique Equipment Search',
    description='Search unique equipment info.',
    response_model=APIResponse[equipment.UniqueWeapon],
)
async def search_uw_req(
    session: SessionDep,
    request: Request,
    payload: equipment.UniqueWeaponRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    eq = await equipment.get_equipment(md, payload)

    if not isinstance(eq, equipment._UniqueWeapon):  # should be impossible
        logger.error(f'Equipment should be a unique weapon\n{str(eq.model_dump_json(indent=4))}')
    eq_resp = equipment.UniqueWeapon(**eq.model_dump(context={'language': language, 'db': session}, exclude_none=True))
    return APIResponse[equipment.UniqueWeapon].create(request, eq_resp)

@router.get(
    '/equipment/upgrade',
    summary='Equipment Upgrade Costs',
    description='Get upgrade costs for equipment. Use /equipment/search or equipment/unique/search for equip_id.',
    response_model=APIResponse[equipment.EquipmentCosts]
)
async def upgrade_cost_req(
    session: SessionDep,
    request: Request,
    payload: equipment.EquipmentCostRequest = Depends(),
    language: Language = Depends(language_parameter)
):
    md: MasterData = request.app.state.md
    costs = await equipment.get_upgrade_costs(md, payload)
    costs_resp = equipment.EquipmentCosts(**costs.model_dump(context={'language': language, 'db': session}, exclude_none=True))
    
    return APIResponse[equipment.EquipmentCosts].create(request, costs_resp)

@router.get(
    '/equipment/{eqp_id}',
    summary='Equipment',
    description='Get equipment info.',
    response_model=Union[APIResponse[equipment.Equipment],APIResponse[equipment.UniqueWeapon]]
)
async def equipment_req(
    session: SessionDep,
    request: Request,
    eqp_id: int,
    language: Language = Depends(language_parameter)
):
    '''Direct equipment id query'''
    md: MasterData = request.app.state.md
    eq = await equipment.get_equipment(md, eqp_id)

    if isinstance(eq, equipment._UniqueWeapon):
        eq_resp = equipment.UniqueWeapon(**eq.model_dump(context={'language': language, 'db': session}, exclude_none=True))
        return APIResponse[equipment.UniqueWeapon].create(request, eq_resp)
    
    eq_resp = equipment.Equipment(**eq.model_dump(context={'language': language, 'db': session}, exclude_none=True))
    return APIResponse[equipment.Equipment].create(request, eq_resp)
