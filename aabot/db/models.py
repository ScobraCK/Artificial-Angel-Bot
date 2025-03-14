from sqlalchemy import Integer, BigInteger, Enum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from aabot.db.database import Base
from aabot.utils.enums import Language, Server

class UserPreference(Base):
    __tablename__ = "user"

    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language: Mapped[Optional[Language]] = mapped_column(Enum(Language))
    server: Mapped[Optional[Server]] = mapped_column(Enum(Server))
    world: Mapped[Optional[int]] = mapped_column(Integer)

class Alias(Base):
    __tablename__ = 'alias'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    char_id: Mapped[int] = mapped_column(Integer)
    alias: Mapped[str] = mapped_column(Text, unique=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)  # Custom vs official names
    

## TODO Emojis https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.fetch_application_emoji