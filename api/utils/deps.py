from fastapi import Depends
from typing import Annotated, Optional, Literal

from api.database import Session
from api.utils.enums import Language

language_codes = Literal['enus']

# Totally not copied from atlas api 
async def language_parameter(language: Optional[Language]=None):
    """Dependency for the language parameter, defaults to Language.enus if none is supplied"""
    if language:
        return language
    else:
        return Language.enus

def get_session():
    with Session() as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
