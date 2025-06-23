from fastapi import Depends
from typing import Annotated, Literal

from common.database import AsyncSession
from common.enums import Language

language_codes = Literal['enus']

# Totally not copied from atlas api 
async def language_parameter(language: Language|None=None):
    """Dependency for the language parameter, defaults to Language.enus if none is supplied"""
    if language:
        return language
    else:
        return Language.enus

async def get_session():
    async with AsyncSession() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
