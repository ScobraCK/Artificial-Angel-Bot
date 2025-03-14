from fastapi import Query
from pydantic import BaseModel, Field, AliasPath, model_validator
from sqlalchemy import Text, Integer, BigInteger, Boolean, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from typing import List, Optional, Literal

from api.database import Base
from api.utils.enums import Server
from api.utils.error import APIError

PlayerCriteria = Literal["bp", "quest", "tower", "azure_tower", "crimson_tower", "emerald_tower", "amber_tower"]

class PlayerORM(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    auto_bp: Mapped[int] = mapped_column(BigInteger)
    bp: Mapped[Optional[int]] = mapped_column(BigInteger)
    rank: Mapped[int] = mapped_column(Integer)
    quest_id: Mapped[int] = mapped_column(Integer)
    tower_id: Mapped[int] = mapped_column(Integer)
    azure_tower_id: Mapped[Optional[int]] = mapped_column(Integer)
    crimson_tower_id: Mapped[Optional[int]] = mapped_column(Integer)
    emerald_tower_id: Mapped[Optional[int]] = mapped_column(Integer)
    amber_tower_id: Mapped[Optional[int]] = mapped_column(Integer)
    icon_id: Mapped[int] = mapped_column(BigInteger)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    guild_join_time: Mapped[Optional[int]] = mapped_column(BigInteger)
    guild_position: Mapped[Optional[int]] = mapped_column(Integer)
    prev_legend_league_class: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[int] = mapped_column(BigInteger)
    
    @validates('guild_id', 'guild_join_time', 'guild_position', 'prev_legend_league_class')
    def validate_none_value(self, key, value):
        return None if value == 0 else value
    
    @hybrid_property
    def server(self) -> int:
        return self.world_id // 1000

    @server.expression
    def server(cls):
        return cls.world_id // 1000

    @hybrid_property
    def world(self) -> int:
        return self.world_id % 1000

    @world.expression
    def world(cls):
        return cls.world_id % 1000

class GuildORM(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    bp: Mapped[int] = mapped_column(BigInteger)
    level: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer)
    exp: Mapped[int] = mapped_column(Integer)
    num_members: Mapped[int] = mapped_column(Integer)
    leader_id: Mapped[int] = mapped_column(BigInteger)
    # policy: Mapped[int] = mapped_column(Integer)  # Deprecated
    description: Mapped[str] = mapped_column(Text)
    free_join: Mapped[bool] = mapped_column(Boolean)
    bp_requirement: Mapped[int] = mapped_column(BigInteger)
    timestamp: Mapped[int] = mapped_column(BigInteger)
    
    @hybrid_property
    def server(self) -> int:
        return self.world_id // 1000

    @server.expression
    def server(cls):
        return cls.world_id // 1000

    @hybrid_property
    def world(self) -> int:
        return self.world_id % 1000

    @world.expression
    def world(cls):
        return cls.world_id % 1000

class PlayerDBModel(BaseModel):
    id: int
    world_id: int
    name: str
    auto_bp: int
    bp: Optional[int]
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

class PlayerRankInfo(BaseModel):
    name: str
    server: int
    world: int
    bp: Optional[int]
    quest_id: Optional[int]
    tower_id: Optional[int]
    azure_tower_id: Optional[int]
    crimson_tower_id: Optional[int]
    emerald_tower_id: Optional[int]
    amber_tower_id: Optional[int]
    timestamp: int
    
    class Config:
        from_attributes = True

class GuildDBModel(BaseModel):
    id: int
    world_id: int
    name: str
    bp: int
    level: int
    stock: int
    exp: int
    num_members: int
    leader_id: int
    description: Optional[str]
    free_join: bool
    bp_requirement: int
    timestamp: int
    
    class Config:
        from_attributes = True

class GuildRankInfo(BaseModel):
    name: str
    server: int
    world: int
    bp: int
    timestamp: int
    
    class Config:
        from_attributes = True

class PlayerRankingRequest(BaseModel):
    count: int = Field(Query(200, gt=0, le=500), description="Number of players to fetch.")
    order_by: PlayerCriteria = Field(Query(...), description="Sorting criteria for ranking.")
    world_id: Optional[List[int]] = Field(Query(None), description="Filter by a list of world IDs")
    server: Optional[Server] = Field(Query(None, description="Filter by server"))

    @model_validator(mode="before")
    @classmethod
    def validate_filters(cls, values):
        if values.get("world_id") and values.get("server"):
            raise APIError("Only one of the filter options world_id, server can be provided.")
        return values
    
class GuildRankingRequest(BaseModel):
    count: int = Field(Query(50, gt=0, le=500), description="Number of guilds to fetch.")
    world_id: Optional[List[int]] = Field(Query(None), description="Filter by a list of world IDs")
    server: Optional[Server] = Field(Query(None, description="Filter by server"))

    @model_validator(mode="before")
    @classmethod
    def validate_filters(cls, values):
        if values.get("world_id") and values.get("server"):
            raise APIError("Only one of the filter options world_id, server can be provided.")
        return values
    