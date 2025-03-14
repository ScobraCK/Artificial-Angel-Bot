import json
import httpx
import asyncio
from typing import Iterator, Optional, List
from api.utils.logger import get_logger

logger = get_logger(__name__)

class MasterData:
    BASE_URL = 'https://raw.githubusercontent.com/ScobraCK/MementoMori-data/main/Master/'

    def __init__(self, preload: bool = False) -> None:
        self.data = {}
        self.catalog = {}
        self.version = None
        self.lock = asyncio.Lock()
        if preload:
            asyncio.create_task(self._preload())

    async def _fetch_version(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{self.BASE_URL}version',
                headers={"Cache-Control": "no-cache"})
            resp.raise_for_status()
            return resp.text.strip()

    async def _fetch_catalog(self) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{self.BASE_URL}master-catalog.json',
                headers={"Cache-Control": "no-cache"})
            resp.raise_for_status()
            return resp.json()['MasterBookInfoMap']

    async def _fetch_MB(self, mb: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{self.BASE_URL}{mb}.json',
                headers={"Cache-Control": "no-cache"},  # remove when testing
                timeout=10
                )
            resp.raise_for_status()
            return resp.json()

    async def _preload(self, exclude: Optional[set] = None) -> List[str]:
        if exclude is None:
            exclude = {'AutoBattleEnemyMB', 'BossBattleEnemyMB'}  # large file
        async with self.lock:
            self.catalog = await self._fetch_catalog()
            self.version = await self._fetch_version()
            updates = [mb for mb in self.catalog.keys() if mb not in exclude]
            tasks = [self._fetch_and_store_mb(mb) for mb in updates]
            await asyncio.gather(*tasks)

        return updates

    async def _fetch_and_store_mb(self, mb: str) -> None:
        self.data[mb] = await self._fetch_MB(mb)

    async def load_MB(self, mb_list: str|List[str]):
        if isinstance(mb_list, str):
            mb_list = [mb_list]
        await self.update_version()  # don't lock while locking
        async with self.lock:
            tasks = [
                self._fetch_and_store_mb(mb)
                for mb in mb_list
            ]
            await asyncio.gather(*tasks)

    async def get_MB(self, mb: str):
        if self.version is None:  # would be only in testing env
            self.version = await self._fetch_version()
        if mb not in self.data:
            async with self.lock:
                await self._fetch_and_store_mb(mb)
                logger.info(f'Added {mb} - {self.version}')
        return self.data[mb]

    async def update_version(self) -> List[str]:
        new_version = await self._fetch_version()
        if new_version == self.version:
            return []

        logger.info(f'Updating Version to {new_version}')
        updates = []
        new_catalog = await self._fetch_catalog()

        async with self.lock:
            tasks = []
            for mb, new_data in new_catalog.items():
                if mb not in self.data:
                    continue
                if new_data['Hash'] != self.catalog.get(mb, {}).get('Hash'):
                    tasks.append(self._fetch_and_store_mb(mb))
                    updates.append(mb)
                    logger.info(f'Updating {mb} - {new_version}')
            await asyncio.gather(*tasks)

            self.version = new_version
            self.catalog = new_catalog
            logger.info('Done updating')
        return updates

    async def search_id(self, id: int, mb: str) -> Optional[dict]:
        mb_data = await self.get_MB(mb)
        return next((item for item in mb_data if item["Id"] == id), None)

    async def search_filter(self, mb: str, **filter_args) -> Iterator[dict]:
        '''
        Common Args:
        - CharacterId (int)
        - RarityFlags (int)
        - JobFlags (int)

        Item Args:
        - ItemId (int)
        - ItemType (int)

        Equipment Args:
        - CompositeId (int)
        - EquipmentLv (int)
        - EquippedJobFlags (int)
        - SlotType (int) [1-6]
        - QualityLv (int) [0-4]
            - 0-1: Non set-gear
            - 1-4: Set-gear
        - Category (int) [1-3]
            - 1: D-S+ rank gear (Non set-gear)
            - 2: Non-UW set-gear
            - 3: UW

        Tower Args:
        - TowerType (int) [1-5]
            - 1: Infinity
            - 2: Azure
            - 3: Crimson
            - 4: Emerald
            - 5: Amber
        - Floor (int)
        '''
        mb_data = await self.get_MB(mb)
        return filter(lambda item: all(item.get(key) == value for key, value in filter_args.items()), mb_data)

    async def search_consecutive(self, mb: str, key, minvalue) -> Iterator[dict]:
        mb_data = await self.get_MB(mb)
        return filter(lambda item: item.get(key) >= minvalue, mb_data)
    