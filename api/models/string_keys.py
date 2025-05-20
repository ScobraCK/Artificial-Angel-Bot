from pydantic import BaseModel, Field
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

import api.database as db

class StringORM(db.Base):
    __tablename__ = 'string_keys'

    key: Mapped[str] = mapped_column(primary_key=True)
    jajp: Mapped[str] = mapped_column(nullable=True)
    kokr: Mapped[str] = mapped_column(nullable=True)
    enus: Mapped[str] = mapped_column(nullable=True)
    zhtw: Mapped[str] = mapped_column(nullable=True)
    dede: Mapped[str] = mapped_column(nullable=True)
    esmx: Mapped[str] = mapped_column(nullable=True)
    frfr: Mapped[str] = mapped_column(nullable=True)
    idid: Mapped[str] = mapped_column(nullable=True)
    ptbr: Mapped[str] = mapped_column(nullable=True)
    ruru: Mapped[str] = mapped_column(nullable=True)
    thth: Mapped[str] = mapped_column(nullable=True)
    vivn: Mapped[str] = mapped_column(nullable=True)
    zhcn: Mapped[str] = mapped_column(nullable=True)


class StringDBModel(BaseModel):
    key: str = Field(examples=['[CharacterName1]'])
    jajp: Optional[str] = Field(None, example="モニカ")
    kokr: Optional[str] = Field(None, example="모니카")
    enus: Optional[str] = Field(None, example="Monica")
    zhtw: Optional[str] = Field(None, example="莫妮卡")
    dede: Optional[str] = Field(None, example="Monica")
    esmx: Optional[str] = Field(None, example="Mónica")
    frfr: Optional[str] = Field(None, example="Monica")
    idid: Optional[str] = Field(None, example="Monica")
    ptbr: Optional[str] = Field(None, example="Mônica")
    ruru: Optional[str] = Field(None, example="Моника")
    thth: Optional[str] = Field(None, example="โมนิก้า")
    vivn: Optional[str] = Field(None, example="Monica")
    zhcn: Optional[str] = Field(None, example="莫妮卡")

    class Config:
        from_attributes = True

class PlayerDBModel(BaseModel):
    id: int
    world_id: int
    name: str
    bp: int
    rank: int
    quest_id: int
    tower_id: int
    azure_tower_id: int
    crimson_tower_id: int
    emerald_tower_id: int
    amber_tower_id: int
    icon_id: int
    guild_id: Optional[int]
    guild_join_time: Optional[int]
    guild_position: Optional[int]
    prev_legend_league_class: Optional[int]
    timestamp: int
    
    class Config:
        from_attributes = True
        