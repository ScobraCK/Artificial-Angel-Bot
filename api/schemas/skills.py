from fastapi import Query
from pydantic import (
    BaseModel, Field, AliasChoices,
    FieldSerializationInfo, field_serializer,
    ValidationInfo, field_validator, model_validator,
    )
from typing import List, Optional, Tuple, Union

from api.utils.masterdata import MasterData
from api.utils.error import APIError
from api.schemas.equipment import search_uw_info, UWDescriptions
import api.schemas.validators as validators
import api.schemas.serializers as serializers
import api.utils.enums as enums

class _PassiveSubSkill(BaseModel):
    trigger: enums.PassiveTrigger = Field(..., validation_alias='PassiveTrigger')
    init_cooltime: int = Field(..., validation_alias='SkillCoolTime')
    max_cooltime: int = Field(..., validation_alias='SkillMaxCoolTime')
    group_id: int = Field(..., validation_alias='PassiveGroupId')
    subskill_id: int = Field(..., validation_alias='SubSetSkillId')

    _serialize_enum = field_serializer(
        'trigger'
    )(serializers.serialize_enum)

class PassiveSubSkill(BaseModel):
    trigger: Optional[str] = Field(...)
    init_cooltime: int = Field(...)
    max_cooltime: int = Field(...)
    group_id: int = Field(...)
    subskill_id: int = Field(...)

class _SkillInfo(BaseModel):
    order_number: int = Field(..., validation_alias='OrderNumber')
    description: str = Field(..., validation_alias='DescriptionKey')
    level: int = Field(..., validation_alias='CharacterLevel')
    uw_rarity: enums.ItemRarity = Field(..., validation_alias='EquipmentRarityFlags')
    blessing_item: int = Field(..., validation_alias='BlessingItemId')
    subskill: Union[List[int], List[_PassiveSubSkill]] = Field(..., validation_alias=AliasChoices('SubSetSkillIds', 'PassiveSubSetSkillInfos'))

    _serialize_str = field_serializer('description')(serializers.serialize_str)
    _serialize_enum = field_serializer('uw_rarity')(serializers.serialize_enum)

class SkillInfo(BaseModel):
    order_number: int = Field(...)
    description: str = Field(...)
    level: int = Field(...)
    uw_rarity: Optional[str] = Field(...)
    blessing_item: int = Field(...)
    subskill: Union[List[int], List[PassiveSubSkill]] = Field(...)

class _ActiveSkill(BaseModel):
    id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    skill_infos: List[_SkillInfo] = Field(..., validation_alias='ActiveSkillInfos')
    condition: str = Field(..., validation_alias='ActiveSkillConditions')
    init_cooltime: int = Field(..., validation_alias='SkillInitCoolTime')
    max_cooltime: int = Field(..., validation_alias='SkillMaxCoolTime')

    _serialize_str = field_serializer('name')(serializers.serialize_str)

class ActiveSkill(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    skill_infos: List[SkillInfo] = Field(...)
    condition: str = Field(...)
    init_cooltime: int = Field(...)
    max_cooltime: int = Field(...)

class _PassiveSkill(BaseModel):
    id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    skill_infos: List[_SkillInfo] = Field(..., validation_alias='PassiveSkillInfos')

    _serialize_str = field_serializer('name')(serializers.serialize_str)

class PassiveSkill(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    skill_infos: List[SkillInfo] = Field(...)

class _Skills(BaseModel):
    character: int
    actives: List[_ActiveSkill]
    passives: List[_PassiveSkill]
    uw_descriptions: Optional[UWDescriptions]

class Skills(BaseModel):
    character: int
    actives: List[ActiveSkill]
    passives: List[PassiveSkill]
    uw_descriptions: Optional[UWDescriptions]

async def find_character_skill_ids(md: MasterData, id: int) -> Tuple[List[int], List[int]]:
    char_data = await md.search_id(id, 'CharacterMB')
    if not char_data:
        raise APIError(f'Could not find character id {id}')

    return char_data.get('ActiveSkillIds'), char_data.get('PassiveSkillIds')

async def find_uw_descriptions(md: MasterData, character: int) -> UWDescriptions|None:
    eq_data = await search_uw_info(md, character)
    if not eq_data:
        return None
    desc_id = eq_data.get('EquipmentExclusiveSkillDescriptionId')
    if desc_id == 0:
        return None
    uw_desc = await md.search_id(desc_id, 'EquipmentExclusiveSkillDescriptionMB')
    return UWDescriptions(**uw_desc)

async def parse_skill(md: MasterData, id: int) -> Union[_ActiveSkill, _PassiveSkill]:
    skill_data = await md.search_id(id, 'ActiveSkillMB')
    if skill_data:  # Active
        return _ActiveSkill(**skill_data)
    else:  # Check Passive
        skill_data = await md.search_id(id, 'PassiveSkillMB')
        if skill_data: # Not found
            return _PassiveSkill(**skill_data)
    raise APIError(f'Could not find skill id of {id}')

async def get_skill_id(md: MasterData, skill_id: int) -> Union[_ActiveSkill, _PassiveSkill]:
    return await parse_skill(md, skill_id)

async def get_skills_char(md: MasterData, char_id: int) -> _Skills:
    active_ids, passives_ids = await find_character_skill_ids(md, char_id)
    actives = []
    passives = []
    for id in active_ids:
        actives.append(await parse_skill(md, id))
    for id in passives_ids:
        passives.append(await parse_skill(md, id))

    uw_desc = await find_uw_descriptions(md, char_id)

    return _Skills(
        character=char_id,
        actives=actives,
        passives=passives,
        uw_descriptions=uw_desc
    )
        