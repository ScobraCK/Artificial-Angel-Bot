import httpx
import html2text
from typing import TypeVar

from async_lru import alru_cache

from aabot.utils.error import BotError, BotAPIError
from common.enums import Language
from common.routes import *  # All API paths moved to common
from common.schemas import APIResponse, CommonStrings, Item, Name, StringKey

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

T = TypeVar('T')

def parse_response(data: dict, data_type: type[T]) -> APIResponse[T]:
    return APIResponse.parse(data, data_type)

async def fetch_api(
    path: str,
    response_model: type[T],
    path_params: dict = None,
    query_params: dict = None,
    headers: dict = None):
    async with httpx.AsyncClient(base_url=API_BASE_PATH, headers=headers) as client:
        if path_params:
            path = path.format(**path_params)
            
        try:
            if query_params:
                params = {k: v for k, v in query_params.items() if v is not None}
            else:
                params = None
            response = await client.get(path, params=params)
            response.raise_for_status()
            data = response.json()
            return parse_response(data, response_model)
            
        except httpx.HTTPStatusError as e:
            if response:
                if response.status_code != 500:
                    error = response.json()  # TODO fix in case of 500
                else:
                    error = {"detail": "Internal Server Error"}
                raise BotAPIError(response.status_code, html2text.HTML2Text().handle(str(error.get('detail', 'No details'))))
            else:
                raise BotError(f"Error in API: Details unknown.")
        except httpx.RequestError as e:
            raise e

async def fetch(
    url: str,
    params: dict = None,
    headers: dict = None,
    base_url: str = '',
    timeout: int=10):
    async with httpx.AsyncClient(headers=headers, base_url=base_url, timeout=timeout) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            raise BotError(f"Error in external API: {url} - {response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f'Timeout fetching {url}: {e}')
            raise e  # Want to get notifications for now
        except httpx.RequestError as e:
            raise e

async def fetch_string(key: str) -> APIResponse[StringKey]:
    string_data = await fetch_api(STRING_PATH.format(key=key), response_model=StringKey)
    return string_data

@alru_cache()
async def fetch_name(char_id: int, language: Language = Language.enus) -> Name:
    '''Does not return APIResponse[Name]. Use for quick access to a single name.'''
    name_data = await fetch_api(
        STRING_CHARACTER_ID_PATH.format(char_id=char_id),
        response_model=Name,
        query_params={'language': language}
    )
    return name_data.data

@alru_cache(ttl=5)
async def fetch_item(item_id: int, item_type: int, language: Language = Language.enus) -> APIResponse[Item]:
    item_data = await fetch_api(
        ITEM_PATH,
        response_model=Item,
        query_params={'item_id': item_id, 'item_type': item_type, 'language': language}
    )
    return item_data

async def fetch_common_strings() -> dict[Language, CommonStrings]:
    data = {}
    for lang in Language:
        lang_data = await fetch_api(
            STRING_COMMON_PATH,
            query_params={'language': lang},
            response_model=CommonStrings
        )
        data[lang] = lang_data.data
    return data
