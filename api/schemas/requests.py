from fastapi import Query
from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional

from api.utils.error import APIError
from common import enums
from common.models import CharacterColumns, PlayerColumns

# Equipment
class EquipmentRequest(BaseModel):
    slot: enums.EquipSlot = Field(Query(..., examples=[1]))
    job: Optional[enums.Job] = Field(Query(None, examples=[1], description='Leave null for non weapons'))
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

# Events
class GachaRequest(BaseModel):
    char_id: Optional[int] = Field(None, description='Character ID to filter by')
    is_active: bool = Field(True, description='Filter by currently active banners')
    include_future: bool = Field(False, description='Includes future banners even when is_active is True. Ignored if is_active is False.')

# Item
class ItemRequest(BaseModel):
    item_id: int = Field(Query())
    item_type: enums.ItemType = Field(Query())

class RuneRequest(BaseModel):
    category: enums.RuneType = Field(..., description='Rune type')
    level: int = Field(..., description='Rune level')

# PvE
class TowerRequest(BaseModel):
    floor: int = Field(Query(..., description='Tower floor'))
    tower_type: enums.TowerType = Field(Query(
        enums.TowerType.Infinity,
        description=(
            'Tower type (Default: Infinity)<br>'
            '1-Infinity<br>2-Azure<br>3-Crimson<br>4-Emerald<br>5-Amber<br>'
        )
    ))



# Mentemori
class PlayerRankingRequest(BaseModel):
    count: int = Field(Query(200, gt=0, le=5000), description="Number of players to fetch.")
    order_by: PlayerColumns = Field(Query(...), description="Sorting criteria for ranking.")
    world_id: Optional[List[int]] = Field(Query(None), description="Filter by a list of world IDs")
    server: Optional[enums.Server] = Field(Query(None, description="Filter by server"))

    @model_validator(mode="before")
    @classmethod
    def validate_filters(cls, values):
        if values.get("world_id") and values.get("server"):
            raise APIError("Only one of the filter options world_id, server can be provided.")
        return values


class GuildRankingRequest(BaseModel):
    count: int = Field(Query(50, gt=0, le=2000), description="Number of guilds to fetch.")
    world_id: Optional[List[int]] = Field(Query(None), description="Filter by a list of world IDs")
    server: Optional[enums.Server] = Field(Query(None, description="Filter by server"))

    @model_validator(mode="before")
    @classmethod
    def validate_filters(cls, values):
        if values.get("world_id") and values.get("server"):
            raise APIError("Only one of the filter options world_id, server can be provided.")
        return values


class CharacterDBRequest(BaseModel):
    option: CharacterColumns = Field(Query(
        ...,
        description=(
            "Parameters<br>"
            "- element: 1: Azure, 2: Crimson, 3: Emerald, 4: Amber, 5: Radiance, 6: Chaos"
            "- job: Values correspond to roles - 1: Warrior, 2: Sniper, 4: Sorcerer<br>"
            "- base_rarity: Acceptable values are 'N', 'R', 'SR'<br>"
            "- Others: Integer"
        )
    ))
    value: Optional[int|Literal['N', 'R', 'SR']] = Field(Query(
        None,
        description='Exact value filter (minvalue and maxvalue should be None when using this)'
    ))
    minvalue: Optional[int] = Field(Query(
        None,
        description='Minimum value'
    ))
    maxvalue: Optional[int] = Field(Query(
        None,
        description='Maximum value'
    ))

    @model_validator(mode='after')
    def validate(self):
        if self.option == 'base_rarity':
            assert isinstance(self.value, str), '"base_rarity" only takes "N", "R", or "SR"'
        else:
            if self.value is not None:
                assert isinstance(self.value, int), '"N", "R", or "SR" should only be used for "base_rarity"'

        if self.value is not None:
            assert self.minvalue is None and self.maxvalue is None, \
                'If "value" is provided, "minvalue" and "maxvalue" cannot be given'
        return self
