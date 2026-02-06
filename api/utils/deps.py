from fastapi import Depends
from typing import Annotated, Literal

from common.database import SessionAA
from common.enums import Language

language_codes = Literal['enus']

async def language_parameter(language: Language|None=None):
    """Dependency for the language parameter, defaults to Language.enus if none is supplied"""
    if language:
        return language
    else:
        return Language.enus

async def get_session():
    async with SessionAA() as session:
        yield session

SessionDep = Annotated[SessionAA, Depends(get_session)]
