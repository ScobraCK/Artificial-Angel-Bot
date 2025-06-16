from sqlalchemy import select, column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.utils.masterdata import MasterData
from common.enums import CharacterRarity
from common.models import CharacterORM, CharacterColumns
from common.schemas import CharacterDBModel

from api.utils.logger import get_logger
logger = get_logger(__name__)

async def upsert_chars(session: AsyncSession, md: MasterData):
    char_data = await md.get_MB('CharacterMB')
    inserted_ids = []

    for char in char_data:
        rarity = CharacterRarity(char['RarityFlags']).name
        try:
            validated_char = CharacterDBModel(**char, base_rarity=rarity)
            char_dict = validated_char.model_dump()
            xmax = column('xmax')  # access system column xmax
            stmt = (
                insert(CharacterORM)
                .values(char_dict)
                .on_conflict_do_update(
                    index_elements=['id'],
                    set_={key: char_dict[key] for key in char_dict if key != 'id'}
                )
                .returning(
                    CharacterORM.id,
                    (xmax == 0).label("inserted")
                )
            )
            result = await session.execute(stmt)
            for row in result:
                if row.inserted:
                    inserted_ids.append(row.id)
        except Exception as e:
            logger.error(f"Failed to update characters - {str(e)}")
            return None

    await session.commit()

    logger.info(f"New characters: {inserted_ids}")

    return inserted_ids

async def get_char(session: AsyncSession, id: int):
    stmt = select(CharacterORM).where(CharacterORM.id == id).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# identical to filtered with no values
async def get_sorted_chars(session: AsyncSession, sorted_by: CharacterColumns):
    col = column(sorted_by)
    stmt = select(CharacterORM).order_by(col, CharacterORM.id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_filtered_chars(session: AsyncSession, filter_by: CharacterColumns, *, value=None, minvalue=None, maxvalue=None):
    col = column(filter_by)
    stmt = select(CharacterORM)
    if value is not None:
        if minvalue is not None or maxvalue is not None:
            raise ValueError('Cannot have a min/max value when value is given')
        stmt = stmt.where(col==value)
    elif minvalue is not None and maxvalue is not None:
        stmt = stmt.where(col.between(minvalue, maxvalue))
    elif minvalue is not None:
        stmt = stmt.where(minvalue <= col)
    elif maxvalue is not None:
        stmt = stmt.where(col <= maxvalue)
    stmt = stmt.order_by(col, CharacterORM.id)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_char_ids(session: AsyncSession):
    '''returns all character ids'''
    stmt = select(CharacterORM.id).order_by(CharacterORM.id)
    result = await session.execute(stmt)
    return result.scalars().all()
