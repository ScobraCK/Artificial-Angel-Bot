from discord import Emoji
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import EmojiORM

async def update_emojis(session: AsyncSession, emojis: list[Emoji]) -> None:
    await session.execute(delete(EmojiORM))
    values = [{'id': emoji.id, 'name': emoji.name} for emoji in emojis]
    stmt = insert(EmojiORM).values(values)
    await session.execute(stmt)
    await session.commit()

async def get_emoji(session: AsyncSession, name: str) -> EmojiORM | None:
    stmt = select(EmojiORM).where(EmojiORM.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
