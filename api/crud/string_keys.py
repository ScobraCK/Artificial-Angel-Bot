from collections import defaultdict
from itertools import batched
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from api.utils.masterdata import MasterData
from common.enums import Language
from common.models import StringORM

from api.utils.logger import get_logger, log_text_changes
logger = get_logger(__name__)
    
async def upsert_string_keys(session: AsyncSession, md: MasterData, update_list=None):
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
            stmt = insert(StringORM).values(batched_values)
            update_dict = {
                c.name: getattr(stmt.excluded, c.name) 
                for c in StringORM.__table__.columns 
                if c.name != 'key'
                }
            stmt = stmt.on_conflict_do_update(index_elements=['key'], set_=update_dict)
            await session.execute(stmt)
    except Exception as e:
        logger.error(f"Failed to update string keys - {str(e)}")

    await session.commit()
        
async def read_all_enus(session: AsyncSession):
    stmt = select(StringORM.key, StringORM.enus)
    result = await session.execute(stmt)
    return result.all()

async def update_and_log_strings(session: AsyncSession, md: MasterData, update_list=None):
    old_text = await read_all_enus(session)
    await upsert_string_keys(session, md, update_list)
    new_text = await read_all_enus(session)
    return log_text_changes(old_text, new_text, md.version)

async def read_string_key(session: AsyncSession, key: str) -> StringORM:
    stmt = select(StringORM).where(StringORM.key==key)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def read_string_key_language(session: AsyncSession, key: str, language: Language) -> str:
    if not isinstance(language, Language):
        raise ValueError(f'{language} is not a recognized language')
    stmt = select(getattr(StringORM, language)).where(StringORM.key==key)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def read_string_key_language_bulk(session: AsyncSession, keys: list[str], language: Language) -> dict[str, str]:
    if not isinstance(language, Language):
        raise ValueError(f'{language} is not a recognized language')

    stmt = select(StringORM.key, getattr(StringORM, language)).where(StringORM.key.in_(keys))
    results = await session.execute(stmt)
    return {key: value for key, value in results.all()}
