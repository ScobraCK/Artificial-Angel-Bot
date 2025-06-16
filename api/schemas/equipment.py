from typing import Optional, Tuple

from api.schemas import requests
from api.utils.error import APIError
from api.utils.masterdata import MasterData
from common import enums, schemas

from api.utils.logger import get_logger
logger = get_logger(__name__)


async def search_equipment(md: MasterData, *, rarity, level, slot=None, job=None, character=None, quality=None)->Tuple[dict, dict]:
    '''
    returns equipment master data. 
    To be used with EquipmentRequest.
    '''
    
    search_args = {
        'RarityFlags': rarity.value if isinstance(rarity, enums.ItemRarity) else rarity,
        'EquipmentLv': level,
    }
    if character:
        # TODO add error checks
        profile_data = await md.search_id(character, 'CharacterProfileMB')
        if profile_data:
            search_args['CompositeId'] = profile_data.get('EquipmentCompositeId', 0)
        else:
            return None, search_args
    else:
        if quality:
            search_args['QualityLv'] = quality
        search_args['SlotType'] = slot
        search_args['EquippedJobFlags'] = job.value if isinstance(job, enums.Job) else job
        search_args['ExclusiveEffectId'] = 0
        
    logger.info(search_args)
    equipment = next(await md.search_filter('EquipmentMB',**search_args), None)

    return equipment, search_args

async def search_uw_info(md: MasterData, character: int):
    '''Only use when general UW data is needed'''
    uw_info, _ = await search_equipment(md, rarity=128, level=180, character=character)  # rarity and level simply set to SSR UW
    return uw_info

async def parse_equipment_upgrades(md: MasterData, is_weapon: bool, start: int=0, target: Optional[int]=None) -> schemas.EquipmentUpgradeData:
    if target and target < start:
        raise APIError(f'Equipment upgrade target level({target}) cannot be lower than start level({start})')
    param_data = await md.get_MB('EquipmentReinforcementParameterMB')
    cost_data = await md.get_MB('EquipmentReinforcementMaterialMB')
    upgrade_key = 'WeaponRequiredItemList' if is_weapon else 'OthersRequiredItemList'

    upgrades = []
    for param, cost in zip(param_data, cost_data):
        level = cost.get('ReinforcementLevel')
        if level < start:  # starts when level == start
            continue
        if target is not None and level > target: # include level == end
            break
        upgrades.append(
            {
                'upgrade_level': level,
                'coefficient': param['ReinforcementCoefficient'], # floored
                'cost': cost[upgrade_key]
            }
        )

    upgrade_data = schemas.EquipmentUpgradeData(is_weapon=is_weapon, upgrades=upgrades)
    return upgrade_data

async def parse_equipment_enhancement(md: MasterData, equipment: schemas.Equipment) -> Tuple[schemas.EquipmentEnhanceLevel, schemas.EquipmentEnhanceRarity]:
    '''
    Gets enhancement data for current equipment
    '''
    level_info = []
    rarity_info = []
    
    # EvolutionType: 1 in EquipmentEvolution data
    # SSR→UR
    if isinstance(equipment, schemas.UniqueWeapon):
        if equipment.rarity >= enums.ItemRarity.UR:
            rarity_info.append(
                schemas.EquipmentEnhanceRarity(
                    before_rarity=enums.ItemRarity.SSR,
                    after_rarity=enums.ItemRarity.UR,
                    cost=[{"ItemCount": 15, "ItemId": 1, "ItemType": 24}]
                )
            )
    # UR→LR
    if equipment.rarity == enums.ItemRarity.LR:
            rarity_info.append(
                schemas.EquipmentEnhanceRarity(
                    before_rarity = enums.ItemRarity.UR,
                    after_rarity=enums.ItemRarity.LR,
                    cost=[{"ItemCount": 50, "ItemId": 1, "ItemType": 24}]
                )
            )
    
    enhance_data = await md.search_id(equipment.evolution_id, 'EquipmentEvolutionMB')
    if enhance_data:
        for evolution_info in enhance_data.get('EquipmentEvolutionInfoList'):
            if evolution_info['BeforeEquipmentLv'] == equipment.level:
                break
            level_info.append(schemas.EquipmentEnhanceLevel(**evolution_info))
    
    return level_info, rarity_info

async def parse_equipment_synthesis(md: MasterData, equipment: schemas.Equipment) -> schemas.EquipmentSynthesis|None:
    costs = []
    if (comp_id := equipment.composite_id) > 0:  # 0 is non synthesis gear
        composite_data = await md.search_id(comp_id, 'EquipmentCompositeMB')
        rarity = composite_data['ItemRarityFlags']
        costs.extend(composite_data['RequiredItemList'])  # gold cost
        costs.append({  # fragments
            "ItemCount": composite_data['RequiredFragmentCount'],
            "ItemId": comp_id,
            "ItemType": 5
        })
        return schemas.EquipmentSynthesis(rarity=rarity, cost=costs)
    return None

async def parse_equipment(md: MasterData, equipment: dict) -> schemas.Equipment:
    '''
    if exclusive effect is not 0, parses into UW
    '''
    set_id = equipment.get('EquipmentSetId')
    set_data = await md.search_id(set_id, 'EquipmentSetMB')

    effect_id = equipment.get('ExclusiveEffectId')
    if effect_id != 0:
        desc_id = equipment.get('EquipmentExclusiveSkillDescriptionId')
        uw_desc = await md.search_id(desc_id, 'EquipmentExclusiveSkillDescriptionMB')
        uw_effect = await md.search_id(effect_id, 'EquipmentExclusiveEffectMB')

        effects = []
        base_effects = uw_effect['BaseParameterChangeInfoList']
        if base_effects:
            effects.extend(base_effects)
        battle_effects = uw_effect['BattleParameterChangeInfoList']
        if battle_effects:
            effects.extend(battle_effects)

        model = schemas.UniqueWeapon(
            **equipment, 
            equipment_set=set_data, 
            character_id=uw_effect['CharacterId'],
            uw_bonus=effects,
            uw_descriptions=uw_desc
            )
    else:
        model = schemas.Equipment(**equipment, equipment_set=set_data)
    return model

async def get_char_id_from_equipment(md: MasterData, equipment: dict)->int:
    effect_id = equipment.get('ExclusiveEffectId')
    uw_effect = await md.search_id(effect_id, 'EquipmentExclusiveEffectMB')
    return uw_effect['CharacterId']

async def get_equipment(md: MasterData, payload: int|requests.EquipmentRequest|requests.UniqueWeaponRequest) -> schemas.Equipment:
    '''
    exclude_none should be included in context
    '''
    if isinstance(payload, requests.EquipmentRequest|requests.UniqueWeaponRequest):
        eq_data, args = await search_equipment(md, **payload.model_dump())
    else:
        eq_data = await md.search_id(payload, 'EquipmentMB')
    if not eq_data:
        raise APIError(f'Could not find equipment matching request<br>Request:{str(payload.model_dump())}<br>Search Args:{args}')
    eq = await parse_equipment(md, eq_data)

    return eq

async def get_upgrade_costs(md: MasterData, payload: requests.EquipmentCostRequest) -> schemas.EquipmentCosts:
    eq_data = await get_equipment(md, payload.equip_id)
    if eq_data.level < payload.upgrade:
        raise APIError('Upgrade level cannot be higher than equipment level')
    
    is_weapon = (eq_data.slot == 1)
    upgrade_costs = await parse_equipment_upgrades(md, is_weapon, target=payload.upgrade)
    synthesis_costs = await parse_equipment_synthesis(md, eq_data)
    enhance_costs, rarity_costs = await parse_equipment_enhancement(md, eq_data)
    
    return schemas.EquipmentCosts(
        equipment=eq_data,
        upgrade_costs=upgrade_costs,
        synthesis_costs=synthesis_costs,
        enhance_costs=enhance_costs,
        rarity_enhance_costs=rarity_costs
    )
