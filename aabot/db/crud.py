from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import List

from aabot.db.models import UserPreference, Alias
from aabot.utils.enums import Language, Server

def update_user(session: Session, uid: int, language: Language = None, server: Server = None, world: int = None) -> UserPreference:
    values = {"language": language, "server": server, "world": world}

    stmt = insert(UserPreference).values(uid=uid, **values)
    stmt = stmt.on_conflict_do_update(
        index_elements=['uid'],
        set_=values
    ).returning(UserPreference)
    
    result = session.execute(stmt)
    session.commit()
    return result.scalar_one()

def delete_user(session: Session, uid: int) -> bool:
    stmt = delete(UserPreference).where(UserPreference.uid == uid)
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0

def get_user(session: Session, uid: int):
    stmt = select(UserPreference).where(UserPreference.uid == uid)
    result = session.execute(stmt)
    return result.scalar_one_or_none()

def insert_alias(session: Session, char_id: int, alias: str, is_custom: bool = False) -> Alias:
    stmt = insert(Alias).values(char_id=char_id, alias=alias, is_custom=is_custom).returning(Alias)
    result = session.execute(stmt)
    session.commit()
    return result.scalar_one()

def get_alias(session: Session, char_id: int) -> List[Alias]:
    stmt = select(Alias).where(Alias.char_id == char_id)
    return session.execute(stmt).scalars().all()

def get_all_alias(session: Session) -> List[Alias]:
    stmt = select(Alias)
    return session.execute(stmt).scalars().all()

def delete_alias(session: Session, alias: str) -> bool:
    stmt = delete(Alias).where(Alias.alias == alias)
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0
    