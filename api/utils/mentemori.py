import httpx

from api.utils.error import MentemoriError

from api.utils.logger import get_logger
logger = get_logger(__name__)

transport = httpx.AsyncHTTPTransport(retries=3)

API_BASE = 'https://api.mentemori.icu/'
GROUP = 'wgroup'
PLAYER = '0/player_ranking/latest'
GUILD = '0/guild_ranking/latest'

async def fetch_mentemori(path: str):
    async with httpx.AsyncClient(base_url=API_BASE, transport=transport) as client:
        try:
            response = await client.get(path)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP error fetching {API_BASE}{path}: {e}')
            raise MentemoriError(f"Failed to get response for {API_BASE}{path}", e)  # Internal error for custom logging
        except httpx.TimeoutException as e:
            logger.error(f'Timeout fetching {API_BASE}{path}: {e}')
            raise e
        except httpx.RequestError as e:
            logger.error(f'Request error fetching {API_BASE}{path}: {e}')
            raise e
        
