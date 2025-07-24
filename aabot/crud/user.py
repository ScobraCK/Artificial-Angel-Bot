from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import Language, Server
from common.models import UserPreference

async def update_user(session: AsyncSession, uid: int, language: Language = None, server: Server = None, world: int = None) -> UserPreference:
    values = {"language": language, "server": server, "world": world}

    stmt = insert(UserPreference).values(uid=uid, **values)
    stmt = stmt.on_conflict_do_update(
        index_elements=['uid'],
        set_=values
    ).returning(UserPreference)
    
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one()

async def delete_user(session: AsyncSession, uid: int) -> bool:
    stmt = delete(UserPreference).where(UserPreference.uid == uid)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

async def get_user(session: AsyncSession, uid: int):
    stmt = select(UserPreference).where(UserPreference.uid == uid)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
    