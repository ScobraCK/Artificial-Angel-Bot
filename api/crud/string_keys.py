from collections import defaultdict
from itertools import batched
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from typing import List

from api.utils.enums import Language
from api.utils.masterdata import MasterData
import api.models.string_keys as skeys

from api.utils.logger import get_logger, log_text_changes
logger = get_logger(__name__)

language_mappings = {
    'jajp': skeys.StringORM.jajp,
    'kokr': skeys.StringORM.kokr,
    'enus': skeys.StringORM.enus,
    'zhtw': skeys.StringORM.zhtw,
}
    
async def upsert_string_keys(session: Session, md: MasterData, update_list=None):
    languages = {
        'JaJp': 'jajp', 
        'KoKr': 'kokr',
        'EnUs': 'enus', 
        'ZhTw': 'zhtw',
        'DeDe': 'dede',
        'EsMx': 'esmx', 
        'FrFr': 'frfr',
        'IdId': 'idid',
        'PtBr': 'ptbr', 
        'RuRu': 'ruru',
        'ThTh': 'thth',
        'ViVn': 'vivn', 
        'ZhCn': 'zhcn'
    }

    text_dict = defaultdict(dict)

    for lang_code, db_field in languages.items():
        mb = f'TextResource{lang_code}MB'
        if update_list and mb not in update_list:  # Only check updated MB
            continue
        text_data = await md.get_MB(mb)

        for text in text_data:
            key = text.get("StringKey")
            text = text.get("Text")
            
            text_dict[key][db_field] = text
        
    values = [
        {'key': key, **translations}
        for key, translations in text_dict.items()
    ]

    try:
        for batched_values in batched(values, 1000):
            stmt = insert(skeys.StringORM).values(batched_values)
            update_dict = {
                c.name: getattr(stmt.excluded, c.name) 
                for c in skeys.StringORM.__table__.columns 
                if c.name != 'key'
                }
            stmt = stmt.on_conflict_do_update(index_elements=['key'], set_=update_dict)
            session.execute(stmt)
    except Exception as e:
        logger.error(f"Failed to update string keys - {str(e)}")

    session.commit()
        
def read_all_enus(session: Session):
    stmt = select(skeys.StringORM.key, skeys.StringORM.enus)
    result = session.execute(stmt).all()
    return result

async def update_and_log_strings(session: Session, md: MasterData, update_list=None):
    old_text = read_all_enus(session)
    await upsert_string_keys(session, md, update_list)
    new_text = read_all_enus(session)
    return log_text_changes(old_text, new_text, md.version)

def read_string_key(session: Session, key: str) -> skeys.StringORM:
    stmt = select(skeys.StringORM).where(skeys.StringORM.key==key)
    return session.scalar(stmt)

def read_string_key_language(session: Session, key: str, language: Language) -> str:
    if not isinstance(language, Language):
        raise ValueError(f'{language} is not a recognized language')
    stmt = select(getattr(skeys.StringORM, language)).where(skeys.StringORM.key==key)
    return session.scalar(stmt)

def read_string_key_language_bulk(session: Session, keys: List[str], language: Language) -> dict[str, str]:
    if not isinstance(language, Language):
        raise ValueError(f'{language} is not a recognized language')

    stmt = select(skeys.StringORM.key, getattr(skeys.StringORM, language)).where(skeys.StringORM.key.in_(keys))
    results = session.execute(stmt).all()

    return {key: value for key, value in results}