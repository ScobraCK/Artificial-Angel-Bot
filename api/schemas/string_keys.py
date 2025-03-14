from pydantic import (
    BaseModel, Field, AliasChoices,
    FieldSerializationInfo, field_serializer,
    ValidationInfo, field_validator, model_validator,
    )
from typing import List, Optional, Dict

import api.schemas.validators as validators
import api.schemas.serializers as serializers
import api.utils.enums as enums
from api.crud.character import get_char_ids
from api.crud.string_keys import read_string_key_language_bulk, read_string_key_language
from api.database import Session
from api.utils.error import APIError

CHARACTER_NAME_KEY = '[CharacterName{}]'
CHARACTER_TITLE_KEY = '[CharacterSubName{}]'

class Name(BaseModel):
    char_id: int
    name: str
    title: Optional[str]

async def get_char_name(session: Session, char_id: int, language: enums.Language) -> Name:
    name_string = read_string_key_language(session, CHARACTER_NAME_KEY.format(char_id), language)
    if not name_string:
        raise APIError(f'[CharacterName{char_id}] does not exist.')
    name = Name(
        char_id = char_id,
        name = name_string,
        title = read_string_key_language(session, CHARACTER_TITLE_KEY.format(char_id), language)
    )
    return name

async def get_char_names(session: Session, language: enums.Language) -> Dict[int, Name]:
    ids = await get_char_ids(session)
    name_keys = [CHARACTER_NAME_KEY.format(id) for id in ids]
    title_keys = [CHARACTER_TITLE_KEY.format(id) for id in ids]
    name_strings = read_string_key_language_bulk(session, name_keys, language)
    title_strings = read_string_key_language_bulk(session, title_keys, language)

    names = { 
        id: Name(
            char_id=id,
            name=name_strings.get(name_key),
            title=title_strings.get(title_key)
        )
        for id, name_key, title_key in zip(ids, name_keys, title_keys)
    }

    return names