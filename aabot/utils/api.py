import httpx
import html2text
from typing import TypeVar

from async_lru import alru_cache

from aabot.utils.error import BotError
from common.enums import Language
from common.schemas import APIResponse, CommonStrings, Item, Name, StringKey

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

API_BASE_PATH = 'http://api:8000/'
STRING_PATH = 'strings/{key}'
STRING_COMMON_PATH = 'strings/common'
STRING_CHARACTER_PATH_ALL = 'strings/character'
STRING_CHARACTER_PATH = 'strings/character/{char_id}'
EQUIPMENT_PATH = 'equipment/{eqp_id}'
EQUIPMENT_NORMAL_PATH = 'equipment/search'
EQUIPMENT_UNIQUE_PATH = 'equipment/unique/search'
EQUIPMENT_UPGRADE_PATH = 'equipment/upgrade'
CHARACTER_LIST_PATH = 'character/list'
CHARACTER_PATH = 'character/{char_id}'
CHARACTER_PROFILE_PATH = 'character/{char_id}/profile'
CHARACTER_LAMENT_PATH = 'character/{char_id}/lament'
CHARACTER_SKILL_PATH = 'character/{char_id}/skill'
CHARACTER_VOICE_PATH = 'character/{char_id}/voiceline'
CHARACTER_MEMORY_PATH = 'character/{char_id}/memory'
ARCANA_PATH = 'arcana'
ITEM_PATH = 'item'
ITEM_RUNE_PATH = 'item/rune'
ITEM_RUNE_CATEGORY_PATH = 'item/rune/{category}'
SKILL_PATH = 'skill/{skill_id}'
QUEST_PATH = 'quest/{quest_id}'
TOWER_PATH = 'tower'
GUILD_RANKING_PATH = 'guild/ranking'
PLAYER_RANKING_PATH = 'player/ranking'
GACHA_PATH = 'gacha'

MASTER_PATH = 'master/{mb}'

UPDATE_PATH = 'admin/update'
UPDATE_STR_PATH = 'admin/update/strings'
UPDATE_CHAR_PATH = 'admin/update/characters'
UPDATE_API_GUILD_PATH = 'admin/mentemori/guilds'
UPDATE_API_PLAYERS_PATH = 'admin/mentemori/players'

MENTEMORI_BASE_PATH = 'https://api.mentemori.icu/'
MENTEMORI_WORLD_PATH = 'worlds'
MENTEMORI_TEMPLE_PATH = '{world_id}/temple/latest'
MENTEMORI_GROUP_PATH = 'wgroups'
MENTEMORI_GACHA_PATH = '{server_id}/{gacha}/latest'
MENTEMORI_RAID_EVENT_PATH = '{world_id}/guild_raid/latest'

T = TypeVar('T')
transport = httpx.AsyncHTTPTransport(retries=3)

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
                raise BotError(f"Error in API: {response.status_code} - {html2text.HTML2Text().handle(str(error.get('detail', 'No details')))}")
            else:
                raise BotError(f"Error in API: Details unknown.")
        except httpx.RequestError as e:
            raise e

async def fetch(
    url: str,
    params: dict = None,
    headers: dict = None,
    base_url: str = '',
    timeout: int=5):
    async with httpx.AsyncClient(headers=headers, base_url=base_url, transport=transport) as client:
        try:
            response = await client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            raise BotError(f"Error in external API: {url} - {response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f'Timeout fetching {url}: {e}')
            raise e  # Want to get notifications for now
            # raise BotError(f'Request has timed out too many times. Please try again later.')
        except httpx.RequestError as e:
            raise e

async def fetch_string(key: str) -> APIResponse[StringKey]:
    string_data = await fetch_api(STRING_PATH.format(key=key), response_model=StringKey)
    return string_data

@alru_cache()
async def fetch_name(char_id: int, language: Language = Language.enus) -> Name:
    '''Does not return APIResponse[Name]. Use for quick access to a single name.'''
    name_data = await fetch_api(
        STRING_CHARACTER_PATH.format(char_id=char_id),
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
