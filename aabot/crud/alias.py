from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import Alias


async def insert_alias(session: AsyncSession, char_id: int, alias: str, is_custom: bool = False) -> Alias:
    stmt = insert(Alias).values(char_id=char_id, alias=alias, is_custom=is_custom).returning(Alias)
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one()


async def get_alias(session: AsyncSession, char_id: int) -> list[Alias]:
    stmt = select(Alias).where(Alias.char_id == char_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_alias(session: AsyncSession) -> list[Alias]:
    stmt = select(Alias)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_alias(session: AsyncSession, alias: str) -> bool:
    stmt = delete(Alias).where(Alias.alias == alias)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0