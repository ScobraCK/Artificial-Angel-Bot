from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.string_keys import read_string_key, translate_keys
from api.schemas.string_keys import get_char_name, get_char_names, get_uw_desc_strings
from api.utils.deps import SessionDep, language_parameter
from api.utils.error import APIError
from common import routes, schemas

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
        routes.STRING_PATH, 
        response_model=schemas.APIResponse[schemas.StringKey],
        description='Examples: CharacterName1, [CharacterName1] <br>While keys should be in brackets("[ExampleKey]") they can be ommited("ExampleKey") and are automatically added'
        )
async def string_lookup(key: str, session: SessionDep, request: Request):
    if not key.startswith('['):
        key = f'[{key}]'
    string_record = await read_string_key(session, key)
    if string_record is None:
        raise APIError(f'Key {key} not found')
    return schemas.APIResponse[schemas.StringKey].create(request, string_record)

@router.get(
    routes.STRING_CHARACTER_PATH,
    summary='Character Name List',
    description='Returns a dict[char_id, Name] of charcter names and titles.',
    response_model=schemas.APIResponse[dict[int, schemas.Name]]
)
async def string_names(session: SessionDep, request: Request, language=Depends(language_parameter)):
    names = await get_char_names(session, language)
    return schemas.APIResponse[dict[int, schemas.Name]].create(request, names)

@router.get(
    routes.STRING_CHARACTER_ID_PATH,
    summary='Character Name',
    description='Returns charcter name and title.',
    response_model=schemas.APIResponse[schemas.Name]
)
async def string_name(session: SessionDep, request: Request, char_id: int, language=Depends(language_parameter)):
    name = await get_char_name(session, char_id, language)
    return schemas.APIResponse[schemas.Name].create(request, name)

@router.get(
    routes.STRING_UW_DESC_PATH,
    summary='UW Descriptions',
    description='Directly gets unique weapon skill description strings for a given character without referencing the actual equipment.',
    response_model=schemas.APIResponse[schemas.UWDescriptions]
)
async def string_uw_descriptions(session: SessionDep, request: Request, char_id: int, language=Depends(language_parameter)):
    uw_descriptions = await get_uw_desc_strings(session, char_id, language)
    if not uw_descriptions:
        raise APIError(f'UW descriptions for character {char_id} in language {language} does not exist.')
    return schemas.APIResponse[schemas.UWDescriptions].create(request, uw_descriptions)

@router.get(
    routes.STRING_COMMON_PATH,
    summary='Common Enum Strings',
    description='Returns a list of common enum strings.',
    response_model=schemas.APIResponse[schemas.CommonStrings]
)
async def string_common(session: SessionDep, request: Request, language=Depends(language_parameter)):
    common_strings = schemas.CommonStrings()
    await translate_keys(common_strings, session, language)
    return schemas.APIResponse[schemas.CommonStrings].create(request, common_strings)
