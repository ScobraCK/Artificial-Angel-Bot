from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.string_keys import read_string_key
from common.schemas import APIResponse, CommonStrings
from api.schemas.string_keys import get_char_name, get_char_names
from api.utils.deps import SessionDep, language_parameter
from api.utils.error import APIError
from api.utils.transformer import Transformer
from common.schemas import Name, StringKey

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
        '/strings/lookup/{key}', 
        response_model=APIResponse[StringKey],
        description='Examples: CharacterName1, [CharacterName1] <br>While keys should be in brackets("[ExampleKey]") they can be ommited("ExampleKey") and are automatically added'
        )
async def string_lookup(key: str, session: SessionDep, request: Request):
    if not key.startswith('['):
        key = f'[{key}]'
    string_record = await read_string_key(session, key)
    if string_record is None:
        raise APIError(f'Key {key} not found')
    return APIResponse[StringKey].create(request, string_record)

@router.get(
    '/strings/character',
    summary='Character Name List',
    description='Returns a dict[char_id, Name] of charcter names and titles . Direct key([ChracterName<ID>]) text search.',
    response_model=APIResponse[dict[int, Name]]
)
async def string_names(session: SessionDep, request: Request, language=Depends(language_parameter)):
    names = await get_char_names(session, language)
    return APIResponse[dict[int, Name]].create(request, names)

@router.get(
    '/strings/character/{char_id}',
    summary='Character Name',
    description='Returns charcter name and title. Direct key([ChracterName<ID>]) text search.',
    response_model=APIResponse[Name]
)
async def string_name(session: SessionDep, request: Request, char_id: int, language=Depends(language_parameter)):
    name = await get_char_name(session, char_id, language)
    return APIResponse[Name].create(request, name)


@router.get(
    '/strings/common',
    summary='Common Enum Strings',
    description='Returns a list of common enum strings.',
    response_model=APIResponse[CommonStrings]
)
async def string_common(session: SessionDep, request: Request, language=Depends(language_parameter)):
    tf = Transformer(session, language)
    common_strings = await tf.transform(CommonStrings())
    return APIResponse[CommonStrings].create(request, common_strings)