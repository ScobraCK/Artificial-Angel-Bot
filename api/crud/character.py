import re

from sqlalchemy import select, column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.crud.string_keys import CHARACTER_NAME_KEY, CHARACTER_TITLE_KEY, read_string_key, read_string_key_language_bulk
from api.utils.masterdata import MasterData
from api.utils.error import APIError
from common.enums import CharacterRarity, Language, LanguageOptions
from common.models import Alias, AltCharacterORM, CharacterORM, CharacterColumns
from common.schemas import CharacterDBModel

from api.utils.logger import get_logger
logger = get_logger(__name__)

# Character table
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
            raise APIError('Cannot have a min/max value when value is given')
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

# Alt table
async def insert_alt(session: AsyncSession, char_id: int, base_id: int) -> None:
    stmt = insert(AltCharacterORM).values(id=char_id, base_id=base_id)
    await session.execute(stmt)
    await session.commit()

async def get_base(session: AsyncSession, char_id: int) -> AltCharacterORM:
    stmt = select(AltCharacterORM).where(AltCharacterORM.id == char_id).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_alts(session: AsyncSession, base_id: int) -> list[AltCharacterORM]:
    stmt = select(AltCharacterORM).where(AltCharacterORM.base_id == base_id).order_by(AltCharacterORM.id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def find_alts(session: AsyncSession, char_id: int) -> list[int]:
    base = await get_base(session, char_id)
    if base:
        base_id = base.base_id
    else:
        base_id = char_id
    alts = await get_alts(session, base_id)
    return [alt.id for alt in alts]

async def update_alt(session: AsyncSession, char_id: int):
    char_ids = await get_char_ids(session)
    keys = {CHARACTER_NAME_KEY.format(id) for id in char_ids}
    names_ = await read_string_key_language_bulk(session, keys, Language.enus)
    name_dict = {int(re.search(r'CharacterName(\d+)', key).group(1)): name for key, name in names_.items()}
    char_name = name_dict.get(char_id)
    if not char_name:
        logger.error(f"Character name for id {char_id} not found when updating alt.")
        return
    matching_names = {k: v for k, v in name_dict.items() if (v == char_name and k != char_id)}
    if len(matching_names) == 0:
        await insert_alt(session, char_id, char_id)
    else:
        base = await get_base(session, min(matching_names.keys()))
        if base:
            await insert_alt(session, char_id, base.base_id)
        else: # Alt DB is initalizing
            if char_id > min(matching_names.keys()):  # matching names excludes self, and base should be lowest
                logger.error(f"Character {char_id} has no base when it should. Char ID: {char_id}, Matching IDs: {matching_names.keys()}")
                return
            await insert_alt(session, char_id, char_id)


# Alias table
# DB tables mainly for AABot use but inserted via API update.
async def insert_alias(session: AsyncSession, char_id: int, alias: str, is_custom: bool = False) -> Alias:
    stmt = (
        insert(Alias)
        .values(char_id=char_id, alias=alias, is_custom=is_custom)
        .on_conflict_do_nothing(index_elements=['alias'])  # Only default alias added, some chars have same alias in differtent languages
    )
    await session.execute(stmt)
    await session.commit()

def normalize_alias(string: str):
    pattern = r"[^\w\s]"
    return re.sub(pattern, '', string).lower()

async def autoalias(session: AsyncSession, char_id: int):
    '''Automatically adds default alias.'''
    serial = len(await find_alts(session, char_id))  # Autoalias should be run after alt update
    names = await read_string_key(session, CHARACTER_NAME_KEY.format(char_id))
    titles = await read_string_key(session, CHARACTER_TITLE_KEY.format(char_id))
    for language in LanguageOptions:
        char_name = getattr(names, language.name)
        if not char_name:
            continue
        if serial > 1:
            char_name = f"{char_name}{serial}"
        await insert_alias(session, char_id, normalize_alias(char_name))
        if titles:
            char_title = getattr(titles, language.name)
            await insert_alias(session, char_id, normalize_alias(char_title))
