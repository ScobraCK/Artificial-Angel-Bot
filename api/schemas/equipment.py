from fastapi import Query
from pydantic import (
    BaseModel, Field, AliasChoices,
    field_serializer, model_validator, FieldSerializationInfo
    )
from typing import List, Optional, Union, Dict, Literal, Tuple

import api.schemas.parameters as params
import api.schemas.serializers as serializers
import api.utils.enums as enums
from api.schemas.items import ItemCount
from api.utils.error import APIError
from api.utils.masterdata import MasterData
from api.utils.deps import language_codes


from api.utils.logger import get_logger
logger = get_logger(__name__)

# Sets
class _SetEffect(BaseModel):
    equipment_count: int = Field(..., validation_alias='RequiredEquipmentCount')
    base_parameter: Optional[params._BaseParameterModel] = Field(None, validation_alias='BaseParameterChangeInfo')
    battle_parameter: Optional[params._BattleParameterModel] = Field(None, validation_alias='BattleParameterChangeInfo')

class SetEffect(BaseModel):
    equipment_count: int = Field(...)
    parameter: Union[params.BaseParameterModel, params.BattleParameterModel] = Field(..., validation_alias=AliasChoices('base_parameter', 'battle_parameter'))

class _EquipmentSet(BaseModel):
    id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    set_effects: List[_SetEffect] = Field(..., validation_alias='EffectList')

    _serialize_str = field_serializer('name')(serializers.serialize_str)

class EquipmentSet(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    set_effects: List[SetEffect] = Field(...)

# Main
class _Equipment(BaseModel):
    equip_id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    icon_id: int = Field(..., validation_alias='IconId')
    slot: enums.EquipSlot = Field(..., validation_alias='SlotType')
    job: enums.Job = Field(..., validation_alias='EquippedJobFlags')
    rarity: enums.ItemRarity = Field(..., validation_alias='RarityFlags')
    quality: int = Field(..., validation_alias='QualityLv')
    level: int = Field(..., validation_alias='EquipmentLv')
    bonus_parameters: int = Field(..., validation_alias='AdditionalParameterTotal')
    basestat: params._BattleParameterModel = Field(..., validation_alias='BattleParameterChangeInfo')
    evolution_id: int = Field(..., validation_alias='EquipmentEvolutionId', exclude=True)
    composite_id: int = Field(..., validation_alias='CompositeId', exclude=True)
    equipment_set: Optional[_EquipmentSet] = None

    @field_serializer('slot')
    def get_equip_type(self, v, info: FieldSerializationInfo):
        context = info.context
        if isinstance(context, dict):
            language = context.get('language', 'enus')
            session = context.get('db', None)

            if session is None:
                raise ValueError('DB session could not be found')
            key = enums.equip_type.get((self.slot, self.job))
            equip_type = serializers.read_string_key_language(session, key, language)
            return equip_type
        else:
            return v  # None

    _serialize_str = field_serializer(
        'name', 'job'
        )(serializers.serialize_str)
    
    _serialize_enum = field_serializer(
        'rarity',
        )(serializers.serialize_enum)

class Equipment(BaseModel):
    equip_id: int = Field(...)
    name: str = Field(...)
    icon_id: int = Field(...)
    slot: str = Field(...)  # replaced equip_type
    job: str = Field(...)
    rarity: str = Field(...)
    quality: int = Field(...)
    level: int = Field(...)
    bonus_parameters: int = Field(...)
    basestat: params.BattleParameterModel = Field(...)
    # evolution_id: int = Field(...)
    # composite_id: int = Field(...)
    equipment_set: Optional[EquipmentSet] = Field(None)

    

# UW
class UWDescriptions(BaseModel):
    SSR: str = Field(..., validation_alias='Description1Key')
    UR: str = Field(..., validation_alias='Description2Key')
    LR: str = Field(..., validation_alias='Description3Key')

    class Config:
        populate_by_name = True
    
    _serialize_str = field_serializer(
        'SSR', 'UR', 'LR'
        )(serializers.serialize_str)

class _UniqueWeapon(_Equipment):
    character_id: int
    uw_bonus: List[Union[params._BaseParameterModel, params._BattleParameterModel]]
    uw_descriptions: UWDescriptions

class UniqueWeapon(Equipment):
    character_id: int = Field(...,)
    uw_bonus: List[Union[params.BaseParameterModel, params.BattleParameterModel]]
    uw_descriptions: UWDescriptions

# Upgrades
class EquipmentUpgradeLevel(BaseModel):
    upgrade_level: int
    coefficient: float
    cost: List[ItemCount]

class EquipmentUpgradeData(BaseModel):
    is_weapon: bool
    upgrades: List[EquipmentUpgradeLevel]   

class EquipmentEnhanceLevel(BaseModel):
    before_level: int = Field(..., validation_alias='BeforeEquipmentLv')
    after_level: int = Field(..., validation_alias='AfterEquipmentLv')
    cost: List[ItemCount] = Field(..., validation_alias='RequiredItemList')

    class Config:
        populate_by_name = True

class _EquipmentSynthesis(BaseModel):
    rarity: enums.ItemRarity
    cost: List[ItemCount]
    
    _serialize_enum = field_serializer(
        'rarity'
        )(serializers.serialize_enum)

class EquipmentSynthesis(BaseModel):
    rarity: str
    cost: List[ItemCount]

class _EquipmentEnhanceRarity(BaseModel):
    before_rarity: enums.ItemRarity
    after_rarity: enums.ItemRarity
    cost: List[ItemCount]   

    _serialize_enum = field_serializer(
        'before_rarity', 'after_rarity'
        )(serializers.serialize_enum)

class EquipmentEnhanceRarity(BaseModel):
    before_rarity: str
    after_rarity: str
    cost: List[ItemCount]   

class _EquipmentCosts(BaseModel): 
    equipment: _Equipment|_UniqueWeapon
    upgrade_costs: EquipmentUpgradeData
    synthesis_costs: Optional[_EquipmentSynthesis]
    enhance_costs: List[EquipmentEnhanceLevel]
    rarity_enhance_costs: List[_EquipmentEnhanceRarity]

class EquipmentCosts(BaseModel): 
    equipment: Equipment|UniqueWeapon
    upgrade_costs: EquipmentUpgradeData
    synthesis_costs: Optional[EquipmentSynthesis] = Field(None)  # Equipment models dump removes None
    enhance_costs: List[EquipmentEnhanceLevel]
    rarity_enhance_costs: List[EquipmentEnhanceRarity]

# Requests
class EquipmentRequest(BaseModel):
    slot: enums.EquipSlot = Field(Query(..., examples=[1]))
    job: Optional[enums.JobFlag] = Field(Query(None, examples=[1], description='Leave null for non weapons'))  # JobFlag for input only
    rarity: enums.ItemRarity = Field(Query(..., examples=[enums.ItemRarity.LR]))
    level: int = Field(Query(..., gt=0, examples=[240]))
    quality: Optional[int] = Field(Query(None, ge=0, le=4, examples=[None], description='S+ equipment have quality of 1. Can omit otherwise.'))

    @model_validator(mode='after')
    def validate(self):
        if self.slot != 1 and self.job:
            raise APIError('Job should be null when slot = 1(Weapon)')
        if self.slot == 1 and not self.job:
            raise APIError('Job should given(1-Warrior, 2-Sniper, or 4-Sorcerer) when slot = 1(Weapon)')
        if not self.job:
            self.job = 7
        return self

class UniqueWeaponRequest(BaseModel):
    rarity: enums.ItemRarity = Field(Query(..., examples=[enums.ItemRarity.LR]))
    level: int = Field(Query(..., gt=0, examples=[240]))
    character: int = Field(Query(..., gt=0, examples=[48]))

class EquipmentUpgradeDataRequest(BaseModel):
    is_weapon: bool
    start: int = Field(Query(1, ge=1))
    end: Optional[int] = Field(Query(None, ge=1))

    @model_validator(mode='after')
    def validate(self):
        if self.end and self.start > self.end:
            raise APIError('Start should be equal or lower than end.')
        
        return self

class EquipmentCostRequest(BaseModel):
    equip_id: int = Field(Query(..., description='Target Equipment. Use /equipment/search or /equipment/unique/search to get id.'))
    upgrade: int = Field(Query(0, ge=0, description='Target upgrade level. Default 0.'))

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

async def parse_equipment_upgrades(md: MasterData, is_weapon: bool, start: int=0, target: Optional[int]=None) -> EquipmentUpgradeData:
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

    upgrade_data = EquipmentUpgradeData(is_weapon=is_weapon, upgrades=upgrades)
    return upgrade_data

async def parse_equipment_enhancement(md: MasterData, equipment: _Equipment) -> Tuple[EquipmentEnhanceLevel, _EquipmentEnhanceRarity]:
    '''
    Gets enhancement data for current equipment
    '''
    level_info = []
    rarity_info = []
    
    # EvolutionType: 1 in EquipmentEvolution data
    # SSR→UR
    if isinstance(equipment, _UniqueWeapon):
        if equipment.rarity >= enums.ItemRarity.UR:
            rarity_info.append(
                _EquipmentEnhanceRarity(
                    before_rarity = enums.ItemRarity.SSR,
                    after_rarity=enums.ItemRarity.UR,
                    cost=[{"ItemCount": 15, "ItemId": 1, "ItemType": 24}]
                )
            )
    # UR→LR
    if equipment.rarity == enums.ItemRarity.LR:
            rarity_info.append(
                _EquipmentEnhanceRarity(
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
            level_info.append(EquipmentEnhanceLevel(**evolution_info))
    
    return level_info, rarity_info

async def parse_equipment_synthesis(md: MasterData, equipment: _Equipment) -> _EquipmentSynthesis|None:
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
        return _EquipmentSynthesis(rarity=rarity, cost=costs)
    return None

async def parse_equipment(md: MasterData, equipment: dict) -> _Equipment:
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

        model = _UniqueWeapon(
            **equipment, 
            equipment_set=set_data, 
            character_id=uw_effect['CharacterId'],
            uw_bonus=effects,
            uw_descriptions=uw_desc
            )
    else:
        model = _Equipment(**equipment, equipment_set=set_data)
    return model

async def get_char_id_from_equipment(md: MasterData, equipment: dict)->int:
    effect_id = equipment.get('ExclusiveEffectId')
    uw_effect = await md.search_id(effect_id, 'EquipmentExclusiveEffectMB')
    return uw_effect['CharacterId']

async def get_equipment(md: MasterData, payload: int|EquipmentRequest|UniqueWeaponRequest) -> _Equipment:
    '''
    exclude_none should be included in context
    '''
    if isinstance(payload, EquipmentRequest|UniqueWeaponRequest):
        eq_data, args = await search_equipment(md, **payload.model_dump())
    else:
        eq_data = await md.search_id(payload, 'EquipmentMB')
    if not eq_data:
        raise APIError(f'Could not find equipment matching request<br>Request:{str(payload.model_dump())}<br>Search Args:{args}')
    eq = await parse_equipment(md, eq_data)

    return eq

async def get_upgrade_costs(md: MasterData, payload: EquipmentCostRequest) -> _EquipmentCosts:
    eq_data = await get_equipment(md, payload.equip_id)
    if eq_data.level < payload.upgrade:
        raise APIError('Upgrade level cannot be higher than equipment level')
    
    is_weapon = (eq_data.slot == 1)
    upgrade_costs = await parse_equipment_upgrades(md, is_weapon, target=payload.upgrade)
    synthesis_costs = await parse_equipment_synthesis(md, eq_data)
    enhance_costs, rarity_costs = await parse_equipment_enhancement(md, eq_data)
    
    return _EquipmentCosts(
        equipment=eq_data,
        upgrade_costs=upgrade_costs,
        synthesis_costs=synthesis_costs,
        enhance_costs=enhance_costs,
        rarity_enhance_costs=rarity_costs
    )
