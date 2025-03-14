from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict

from api.utils.deps import SessionDep, language_parameter
from api.crud.string_keys import read_string_key
from api.models.string_keys import StringDBModel
from api.schemas.api_models import APIResponse
from api.schemas import string_keys as skey_schemas
from api.utils.error import APIError


from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
        '/strings/lookup/{key}', 
        response_model=APIResponse[StringDBModel],
        description='Examples: CharacterName1, [CharacterName1] <br>While keys should be in brackets("[ExampleKey]") they can be ommited("ExampleKey") and are automatically added'
        )
async def string_lookup(key: str, session: SessionDep, request: Request):
    if not key.startswith('['):
        key = f'[{key}]'
    string_record = read_string_key(session, key)
    if string_record is None:
        raise APIError(f'Key {key} not found')
    return APIResponse[StringDBModel].create(request, string_record)

@router.get(
    '/strings/characters',
    summary='Character Name List',
    description='Returns a dict[char_id, Name] of charcter names and titles . Direct key([ChracterName<ID>]) search.',
    response_model=APIResponse[Dict[int, skey_schemas.Name]]
)
async def string_names(session: SessionDep, request: Request, language=Depends(language_parameter)):
    names = await skey_schemas.get_char_names(session, language)
    return APIResponse[Dict[int, skey_schemas.Name]].create(request, names)

@router.get(
    '/strings/characters/{char_id}',
    summary='Character Name',
    description='Returns charcter name and title. Direct key([ChracterName<ID>]) search.',
    response_model=APIResponse[skey_schemas.Name]
)
async def string_name(session: SessionDep, request: Request, char_id: int, language=Depends(language_parameter)):
    name = await skey_schemas.get_char_name(session, char_id, language)
    return APIResponse[skey_schemas.Name].create(request, name)
