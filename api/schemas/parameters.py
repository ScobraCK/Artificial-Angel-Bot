from pydantic import BaseModel, Field, field_serializer, model_validator

from api.schemas import serializers
from api.utils.enums import BaseParameter, BattleParameter

PERCENTAGE_PARAMS = [
    BattleParameter.CRIT_DMG_BOOST,
    BattleParameter.M_CRIT_DMG_CUT,
    BattleParameter.P_CRIT_DMG_CUT,
    BattleParameter.COUNTER,
    BattleParameter.HP_DRAIN
]

class _BaseParameterModel(BaseModel):
    type: BaseParameter = Field(..., alias='BaseParameterType')
    change_type: int = Field(..., alias='ChangeParameterType') 
    value: int = Field(..., alias='Value')

    _serialize_str = field_serializer('type')(serializers.serialize_str)


class BaseParameterModel(BaseModel):
    type: str = Field(..., examples=['STR'])
    change_type: int = Field(..., examples=[1], description='1: +Value | 2: Value% | 3: +Value/Lv') 
    value: int = Field(..., examples=[1000])

class _BattleParameterModel(BaseModel):
    type: BattleParameter = Field(..., alias='BattleParameterType')
    change_type: int = Field(..., alias='ChangeParameterType') 
    value: int = Field(..., alias='Value')
    is_percentage: bool = Field(False)

    _serialize_str = field_serializer('type')(serializers.serialize_str)
    
    @model_validator(mode='after')
    def check_percentage(self):
        '''Shows if the value is a percent value or flat value'''
        if self.type in PERCENTAGE_PARAMS:
            self.is_percentage=True
        return self

class BattleParameterModel(BaseModel):
    type: str = Field(..., examples=['ATK'])
    change_type: int = Field(..., examples=[1], description='1: +Value | 2: Value% | 3: +Value/Lv')
    value: int = Field(..., examples=[1000])
    is_percentage: bool

class BaseParameters(BaseModel):
    str: int = Field(validation_alias='Muscle')
    dex: int = Field(validation_alias='Energy')
    mag: int = Field(validation_alias='Intelligence')
    sta: int = Field(validation_alias='Health')

    class Config:
        populate_by_name = True

class BattleParameters(BaseModel):
    hp: int = Field(..., validation_alias="HP")
    attack: int = Field(..., validation_alias="AttackPower")
    defense: int = Field(..., validation_alias="Defense")
    def_break: int = Field(..., validation_alias="DefensePenetration")
    speed: int = Field(..., validation_alias="Speed")
    pmdb: int = Field(..., validation_alias="DamageEnhance")
    acc: int = Field(..., validation_alias="Hit")
    crit: int = Field(..., validation_alias="Critical")
    crit_dmg: int = Field(..., validation_alias="CriticalDamageEnhance")
    debuff_acc: int = Field(..., validation_alias="DebuffHit")
    counter: int = Field(..., validation_alias="DamageReflect")
    pdef: int = Field(..., validation_alias="PhysicalDamageRelax")
    mdef: int = Field(..., validation_alias="MagicDamageRelax")
    evade: int = Field(..., validation_alias="Avoidance")
    crit_res: int = Field(..., validation_alias="CriticalResist")
    pcut: int = Field(..., validation_alias="PhysicalCriticalDamageRelax")
    mcut: int = Field(..., validation_alias="MagicCriticalDamageRelax")
    debuff_res: int = Field(..., validation_alias="DebuffResist")
    hp_drain: int = Field(..., validation_alias="HpDrain")

    class Config:
        populate_by_name = True