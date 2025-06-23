
from typing import Any

from pydantic import BaseModel

from api.crud.string_keys import read_string_key_language
from common import enums
from sqlalchemy.ext.asyncio import AsyncSession

class Transformer:
    """
    Converts string keys to their respective language values
    """
    def __init__(self, db: AsyncSession, language: enums.Language):
        self.db = db
        self.language = language

    async def transform(self, data: Any) -> dict[str, Any]:
        if isinstance(data, list):
            return [(await self.transform(item)) for item in data]
        elif isinstance(data, dict):
            return {key: (await self.transform(value)) for key, value in data.items()}
        elif isinstance(data, BaseModel):
            return {key: (await self.transform(value)) for key, value in data.model_dump().items()}
        elif isinstance(data, str) and (data.startswith('[') and data.endswith(']')):
            # String Key
            if self.db is None:
                raise ValueError('DB session could not be found')
            return await read_string_key_language(self.db, data, self.language)  # None is allowed, handle afterwards
        else:
            return data
