from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import CharacterORM

async def get_character(session: AsyncSession, char_id: int) -> CharacterORM:
    result = await session.execute(select(CharacterORM).where(CharacterORM.id == char_id))
    return result.scalar_one()
