from sqlalchemy.ext.asyncio import AsyncSession

from api.crud.character import get_char_ids
from api.crud.string_keys import read_string_key_language_bulk, read_string_key_language
from api.utils.error import APIError
from common import enums, schemas

CHARACTER_NAME_KEY = '[CharacterName{}]'
CHARACTER_TITLE_KEY = '[CharacterSubName{}]'

async def get_char_name(session: AsyncSession, char_id: int, language: enums.Language) -> schemas.Name:
    name_string = await read_string_key_language(session, CHARACTER_NAME_KEY.format(char_id), language)
    if not name_string:
        raise APIError(f'[CharacterName{char_id}] for language {language} does not exist.')
    name = schemas.Name(
        char_id = char_id,
        name = name_string,
        title = await read_string_key_language(session, CHARACTER_TITLE_KEY.format(char_id), language)
    )
    return name

async def get_char_names(session: AsyncSession, language: enums.Language) -> dict[int, schemas.Name]:
    ids = await get_char_ids(session)
    name_keys = [CHARACTER_NAME_KEY.format(id) for id in ids]
    title_keys = [CHARACTER_TITLE_KEY.format(id) for id in ids]
    name_strings = await read_string_key_language_bulk(session, name_keys, language)
    title_strings = await read_string_key_language_bulk(session, title_keys, language)

    names = { 
        id: schemas.Name(
            char_id=id,
            name=name_strings.get(name_key),
            title=title_strings.get(title_key)
        )
        for id, name_key, title_key in zip(ids, name_keys, title_keys)
    }

    return names
