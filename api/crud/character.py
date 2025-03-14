from sqlalchemy.orm import Session
from sqlalchemy import select, column
from sqlalchemy.dialects.postgresql import insert

from api.models.character import CharacterORM, CharacterDBModel, CharacterColumns
import api.utils.masterdata as masterdata
from api.utils.enums import CharacterRarity

from api.utils.logger import get_logger
logger = get_logger(__name__)

async def upsert_chars(session: Session, md: masterdata.MasterData):
    char_data = await md.get_MB('CharacterMB')
    profile_data = await md.get_MB('CharacterProfileMB')
    release_check = {char['Id'] for char in profile_data}  # Only update released characters
    inserted_ids = []

    for char in char_data:
        rarity = CharacterRarity(char['RarityFlags']).name
        try:
            validated_char = CharacterDBModel(**char, base_rarity=rarity)
            if validated_char.id not in release_check:  # Only update released characters
                continue
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
            result = session.execute(stmt)
            for row in result:
                if row.inserted:
                    inserted_ids.append(row.id)
        except Exception as e:
            logger.error(f"Failed to update characters - {str(e)}")
            return None

    session.commit()

    logger.info(f"New characters: {inserted_ids}")

    return inserted_ids

async def get_char(session: Session, id: int):
    stmt = select(CharacterORM).where(CharacterORM.id == id).limit(1)
    return session.scalar(stmt)

# identical to filtered with no values
async def get_sorted_chars(session: Session, sorted_by: CharacterColumns):
    col = column(sorted_by)
    stmt = select(CharacterORM).order_by(col, CharacterORM.id)
    return session.scalars(stmt).all()

async def get_filtered_chars(session: Session, filter_by: CharacterColumns, *, value=None, minvalue=None, maxvalue=None):
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
    
    return session.scalars(stmt).all()

async def get_char_ids(session: Session):
    '''returns all character ids'''
    stmt = select(CharacterORM.id).order_by(CharacterORM.id)
    return session.scalars(stmt).all()