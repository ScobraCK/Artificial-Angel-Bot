from sqlalchemy import BigInteger, Boolean, Enum, Integer, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, validates
from typing import Literal

from common.database import Base
from common.enums import Language, Server

# column filter option 
CharacterColumns = Literal['id', 'speed', 'element', 'job', 'base_rarity']
PlayerColumns = Literal["bp", "quest", "rank", "tower", "azure_tower", "crimson_tower", "emerald_tower", "amber_tower"]

class CharacterORM(Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True)
    speed: Mapped[int]
    element: Mapped[int]
    job: Mapped[int]
    base_rarity: Mapped[Literal['N', 'R', 'SR']]
    # xmax: Mapped[str] = mapped_column(system=True)  # to find changes during upsert, instead using column() during crud

class PlayerORM(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    world_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    bp: Mapped[int] = mapped_column(BigInteger)
    rank: Mapped[int] = mapped_column(Integer)
    quest_id: Mapped[int] = mapped_column(Integer)
    tower_id: Mapped[int] = mapped_column(Integer)
    azure_tower_id: Mapped[int|None] = mapped_column(Integer)
    crimson_tower_id: Mapped[int|None] = mapped_column(Integer)
    emerald_tower_id: Mapped[int|None] = mapped_column(Integer)
    amber_tower_id: Mapped[int|None] = mapped_column(Integer)
    icon_id: Mapped[int] = mapped_column(BigInteger)
    guild_id: Mapped[int|None] = mapped_column(BigInteger)
    guild_join_time: Mapped[int|None] = mapped_column(BigInteger)
    guild_position: Mapped[int|None] = mapped_column(Integer)
    prev_legend_league_class: Mapped[int|None] = mapped_column(Integer)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
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

class StringORM(Base):
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

# AABot only
class UserPreference(Base):
    __tablename__ = "user"

    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language: Mapped[Language|None] = mapped_column(Enum(Language))
    server: Mapped[Server|None] = mapped_column(Enum(Server))
    world: Mapped[int|None] = mapped_column(Integer)

class Alias(Base):
    __tablename__ = 'alias'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    char_id: Mapped[int] = mapped_column(Integer)
    alias: Mapped[str] = mapped_column(Text, unique=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)  # Custom vs official names
    
## TODO Emojis https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.fetch_application_emoji