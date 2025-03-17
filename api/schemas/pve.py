from fastapi import Query
from pydantic import (
    BaseModel, Field, AliasPath,
    FieldSerializationInfo, field_serializer,
    ValidationInfo, field_validator, model_validator,
    )
from typing import List, Optional, Literal, Union, Any

from api.schemas.items import ItemCount
from api.schemas.parameters import BaseParameters, BattleParameters
from api.utils.error import APIError
from api.utils.masterdata import MasterData
import api.schemas.validators as validators
import api.schemas.serializers as serializers
import api.utils.enums as enums

from api.utils.logger import get_logger
logger = get_logger(__name__)

class _Enemy(BaseModel):
    enemy_id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    bp: int = Field(..., validation_alias='BattlePower')
    icon_type: enums.UnitIconType = Field(..., validation_alias='UnitIconType')
    icon_id: int = Field(..., validation_alias='UnitIconId')
    element: enums.Element = Field(..., validation_alias='ElementType')
    rarity: enums.CharacterRarity = Field(..., validation_alias='CharacterRarityFlags')
    job: enums.Job = Field(..., validation_alias='JobFlags')
    level: int = Field(..., validation_alias='EnemyRank')
    base_params: BaseParameters = Field(..., validation_alias='BaseParameter')
    battle_params: BattleParameters = Field(..., validation_alias='BattleParameter')
    attack_type: enums.NormalSkill = Field(..., validation_alias='NormalSkillId')
    actives: List[int] = Field(..., validation_alias='ActiveSkillIds')
    passives: List[int] = Field(..., validation_alias='PassiveSkillIds')
    uw_rarity: enums.ItemRarity = Field(..., validation_alias='ExclusiveEquipmentRarityFlags')

    _serialize_str = field_serializer(
        'name', 'element', 'job'
        )(serializers.serialize_str)

    _serialize_enum = field_serializer(
        'rarity', 'attack_type', 'uw_rarity'
    )(serializers.serialize_enum)

class Enemy(BaseModel):
    enemy_id: int = Field(...)  # {UnitType}{quest_id:05d}{slot:02d}
    name: str = Field(...)
    bp: int = Field(...)
    icon_type: int = Field(...)
    icon_id: int = Field(...)
    element: str = Field(...)
    rarity: str = Field(...)
    job: str = Field(...)
    level: int = Field(...)
    base_params: BaseParameters = Field(...)
    battle_params: BattleParameters = Field(...)
    attack_type: str = Field(...)
    actives: List[int] = Field(...)
    passives: List[int] = Field(...)
    uw_rarity: Optional[str] = Field(...)

class _Quest(BaseModel):
    quest_id: int = Field(..., validation_alias='Id')
    chapter: int = Field(..., validation_alias='ChapterId')
    enemy_list: List[_Enemy]
    gold: int = Field(..., validation_alias='GoldPerMinute')
    red_orb: int = Field(..., validation_alias='PotentialJewelPerDay')
    population: int = Field(..., validation_alias='Population')
    # min_green_orb: int
    # min_exp

class Quest(BaseModel):
    quest_id: int = Field(...)
    chapter: int = Field(...)
    gold: int = Field(...)
    red_orb: int = Field(...)
    population: int = Field(...)
    enemy_list: List[Enemy] = Field(...)

class _Tower(BaseModel):
    tower_id: int = Field(..., validation_alias='Id')
    tower_type: enums.TowerType = Field(..., validation_alias='TowerType')
    floor: int = Field(..., validation_alias='Floor')
    fixed_rewards: Optional[List[ItemCount]] = Field(..., validation_alias='BattleRewardsConfirmed')
    first_rewards: Optional[List[ItemCount]] = Field(..., validation_alias='BattleRewardsFirst')
    enemy_list: List[_Enemy]

    _serialize_enum = field_serializer(
        'tower_type'
    )(serializers.serialize_enum)
    

class Tower(BaseModel):
    tower_id: int = Field(...)
    tower_type: str = Field(...)
    floor: int = Field(...)
    fixed_rewards: Optional[List[ItemCount]] = Field(...)
    first_rewards: Optional[List[ItemCount]] = Field(...)
    enemy_list: List[Enemy] = Field(...)

# Request
class TowerRequest(BaseModel):
    floor: int = Field(Query(..., description='Tower floor'))
    tower_type: enums.TowerType = Field(Query(
        enums.TowerType.Infinity,
        description=(
            'Tower type (Default: Infinity)<br>'
            '1-Infinity<br>2-Azure<br>3-Crimson<br>4-Emerald<br>5-Amber<br>'
        )
    ))

async def parse_quest_enemies(md: MasterData, quest_id: int) -> List[dict]:
    first_enemy = int(f'{enums.EnemyType.BossBattle}{quest_id:05d}01')
    end = int(f'{enums.EnemyType.BossBattle}{quest_id+1:05d}00') # id must be lower than end
    enemy_it = await md.search_consecutive('BossBattleEnemyMB', 'Id', first_enemy)
    enemies = []
    for enemy in enemy_it:
        if enemy['Id'] > end:
            break
        enemies.append(enemy)
    
    return enemies

async def parse_tower_enemies(md: MasterData, enemy_list: List[int]) -> List[dict]:
    first_enemy = enemy_list[0]
    enemy_it = await md.search_consecutive('TowerBattleEnemyMB', 'Id', first_enemy)
    enemies = []
    for enemy in enemy_it:
        if enemy.get('Id') not in enemy_list:
            break
        enemies.append(enemy)
    
    if len(enemy_list) != len(enemies):
        logger.error(f'Enemy data was incorrect: {enemy_list}')

    return enemies

async def get_quest(md: MasterData, quest_id: int) -> _Quest:
    quest_data = await md.search_id(quest_id, 'QuestMB')
    if not quest_data:
        raise APIError(f'Quest id {quest_id} not found')
    enemies = await parse_quest_enemies(md, quest_id)
    return _Quest(**quest_data, enemy_list=enemies)

async def get_tower(md: MasterData, payload: TowerRequest) -> _Tower:
    args = {
        'Floor': payload.floor,
        'TowerType': payload.tower_type
    }
    try:
        tower_data = next(await md.search_filter('TowerBattleQuestMB', **args))
    except StopIteration:
        raise APIError(f'Tower {payload.tower_type} floor {payload.floor} not found')
    enemies = await parse_tower_enemies(md, tower_data.get('EnemyIds'))
    return _Tower(**tower_data, enemy_list=enemies)
