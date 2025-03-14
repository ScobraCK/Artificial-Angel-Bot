from fastapi import Query
from pydantic import BaseModel, Field, AliasPath, model_validator
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from typing import Literal, Optional

import api.database as db

CharacterColumns = Literal[
    'id',
    'speed',
    'element',
    'job',
    'base_rarity'
]

class CharacterORM(db.Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True)
    speed: Mapped[int]
    element: Mapped[int]
    job: Mapped[int]
    base_rarity: Mapped[Literal['N', 'R', 'SR']]
    # xmax: Mapped[str] = mapped_column(system=True)

class CharacterDBModel(BaseModel):
    id: int = Field(validation_alias='Id')
    speed: int = Field(validation_alias=AliasPath('InitialBattleParameter', 'Speed'))
    element: int = Field(validation_alias='ElementType')
    job: int = Field(validation_alias='JobFlags')
    base_rarity: Literal['N', 'R', 'SR']

    class Config:
        from_attributes = True
        populate_by_name = True

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
    