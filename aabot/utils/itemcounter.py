from asyncio import gather
from collections import defaultdict
from typing import Union

from sqlalchemy.ext.asyncio import AsyncSession

from aabot.utils import api
from aabot.utils.emoji import to_emoji
from common import enums, schemas
from common.database import SessionAA

async def item_count_string(itemcount: schemas.ItemCount, session: AsyncSession=None, language: enums.Language=enums.Language.enus) -> str:
    item_data = await api.fetch_item(itemcount.item_id, itemcount.item_type)
    item = item_data.data
    if not session:  # called from ItemCounter(asyncio.gather)
        async with SessionAA() as session_:
            return f'{await to_emoji(session_, item)}×{itemcount.count:,}'
    else:
        return f'{await to_emoji(session, item)}×{itemcount.count:,}'

class ItemCounter:
    def __init__(self, language: enums.Language=enums.Language.enus, blacklist:list[enums.ItemType] = []):
        self.items = defaultdict(int)  # Stores (item_id, item_type) -> count
        self.blacklist = blacklist  # type blacklist
        self.language=language

    def add_items(self, items: Union[schemas.ItemCount, list[schemas.ItemCount], 'ItemCounter']):
        if isinstance(items, schemas.ItemCount):  # Single item
            self.items[(items.item_id, items.item_type)] += items.count
        elif isinstance(items, list):  # List of items
            for item in items:
                if not isinstance(item, schemas.ItemCount):
                    raise TypeError("List must contain only ItemCount instances")
                self.items[(item.item_id, item.item_type)] += item.count
        elif isinstance(items, ItemCounter):  # Another ItemCounter
            for (item_id, item_type), count in items.items.items():
                self.items[(item_id, item_type)] += count
        else:
            raise TypeError("Expected ItemCount, list[ItemCount], or ItemCounter")

    def get_total(self) -> list[schemas.ItemCount]:
        return [schemas.ItemCount(item_id=item_id, item_type=item_type, count=count) for (item_id, item_type), count in self.items.items() if item_type not in self.blacklist]

    async def get_total_strings(self) -> list[str]:
        return await gather(*(item_count_string(item, None, self.language) for item in self.get_total()))

    def clear(self) -> None:
        self.items.clear()

    def __bool__(self) -> bool:
        return bool(self.items)