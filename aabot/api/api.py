import httpx
import html2text
from typing import Type, TypeVar, Optional, Any, Union

from aabot.api import response
from aabot.utils.enums import Language
from aabot.utils.error import BotError

API_BASE_PATH = 'http://api:8000/'
STRING_PATH = 'strings/{key}'
STRING_CHARACTER_PATH_ALL = 'strings/characters'
STRING_CHARACTER_PATH = 'strings/characters/{char_id}'
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
ITEM_PATH = 'item'
SKILL_PATH = 'skill/{skill_id}'
QUEST_PATH = 'quest/{quest_id}'
TOWER_PATH = 'tower'
GUILD_RANKING_PATH = 'guild/ranking'
PLAYER_RANKING_PATH = 'player/ranking'
GACHA_PATH = 'gacha'

RAW_MASTER = 'raw/master/{mb}'

UPDATE_PATH = 'admin/update'
UPDATE_STR_PATH = 'admin/update/strings'
UPDATE_CHAR_PATH = 'admin/update/characters'
UPDATE_API_GUILD_PATH = 'admin/mentemori/guilds'
UPDATE_API_PLAYERS_PATH = 'admin/mentemori/players'

MENTEMORI_BASE_PATH = 'https://api.mentemori.icu/'
MENTEMORI_TEMPLE_PATH = '{world_id}/temple/latest'
MENTEMORI_GROUP_PATH = 'wgroups'
MENTEMORI_GACHA_PATH = '{server_id}/{gacha}/latest'

T = TypeVar('T')

def parse_response(data: dict, data_type: Type[T]) -> response.APIResponse[T]:
    return response.APIResponse.parse(data, data_type)

async def fetch_api(
    path: str,
    response_model: Type[T],
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
                error = response.json()  # TODO fix in case of 500
                raise BotError(f"Error in API: {response.status_code} - {html2text.HTML2Text().handle(error.get('error', 'No details'))}")
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
    async with httpx.AsyncClient(headers=headers, base_url=base_url) as client:
        try:
            response = await client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            raise BotError(f"Error in external API: {url} - {response.status_code}")
        except httpx.RequestError as e:
            raise e

async def fetch_string(key: str) -> response.APIResponse[response.StringDBModel]:
    string_data = await fetch_api(STRING_PATH.format(key=key), response_model=response.StringDBModel)
    return string_data

async def fetch_name(char_id: int, language: Language = Language.enus) -> response.APIResponse[response.Name]:
    name_data = await fetch_api(
        STRING_CHARACTER_PATH.format(char_id=char_id),
        response_model=response.Name,
        query_params={'language': language}
    )
    return name_data

async def fetch_item(item_id: int, item_type: int, language: Language = Language.enus) -> response.APIResponse[response.Item]:
    item_data = await fetch_api(
        ITEM_PATH,
        response_model=response.Item,
        query_params={'item_id': item_id, 'item_type': item_type, 'language': language}
    )
    return item_data
