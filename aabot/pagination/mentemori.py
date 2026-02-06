from enum import Enum
from io import StringIO
from itertools import batched
from functools import partial
from re import split

from discord import ui

from aabot.pagination.view import BaseContainer
from aabot.utils import api
from aabot.utils.error import BotError, BotAPIError
from aabot.utils.emoji import to_emoji, character_string
from aabot.utils.itemcounter import ItemCounter, item_count_string
from aabot.utils.utils import from_quest_id, from_world_id, to_world_id, make_table
from common import schemas
from common.database import SessionAA
from common.enums import ItemType, Language, Server

class PlayerCategory(Enum):
    BP = 'bp'
    Quest = 'quest'
    Rank = 'rank'

class TowerCategory(Enum):
    Infinity = 'tower'
    Azure = 'azure_tower'
    Crimson = 'crimson_tower'
    Emerald = 'emerald_tower'
    Amber = 'amber_tower'

class GachaLog(Enum):
    IoC = 'destiny_log'
    IoSG = 'stars_guidance_log'

# For Gacha Logs
game_server = {
    1: ['jp1', 'jp2', 'jp3', 'jp4', 'jp5'],
    2: ['kr1', 'kr2'],
    3: ['ap1', 'ap2'],
    4: ['us1'],
    5: ['eu1'],
    6: ['gl1', 'gl2']
}

class MentemoriContainer(BaseContainer):
    def add_timestamp(self, timestamp: int):
        self.add_item(ui.TextDisplay(f'Timestamp: <t:{timestamp}:R>'))
        return self

    def add_ranking_update_footer(self):
        self.add_item(ui.TextDisplay('-# Updates every hour'))
        return self

def world_ids_help():
    text = (
        "**World Id Help**\n"
        'World Ids are 4 digit integers in the format of SWWW, where S is the server id and W is the world.\n'
        'Server. 1 = Japan, 2 = Korea, 3 = Asia, 4 = North America, 5 = Europe, 6 = Global\n\n'
        'Examples:\n'
        '```\n'
        'JP1: 1001\n'
        'JP101: 1101\n'
        'NA1: 4001\n```'
    )

    return text

# temple_type = {
#     1: 'green_orb',
#     2: 'water',
#     3: 'red_pot',
#     4: 'red_orb',
#     5: 'rune_ticket'
# }

async def temple_ui(server: Server, world: int):
    container = MentemoriContainer(f'### Temple {server.name} W{world}')
    ic = ItemCounter()
    try:
        resp = await api.fetch(
            api.MENTEMORI_TEMPLE_PATH.format(world_id=to_world_id(server, world)),
            base_url=api.MENTEMORI_BASE_PATH
        )
    except BotAPIError as e:
        if e.status_code == 404:
            raise BotError(f'Temple data not found for {server.name} W{world}. Check if the server and world is correct. New worlds may take a while for data to appear.')
        else:
            raise e
    data = resp.json()
    quests = data['data']['quests']

    async with SessionAA() as session:
        container.add_item(ui.TextDisplay(f'Lv. {int(str(quests[0]["Id"])[1:4])}'))

        for quest in quests[::-1]:
            quest_text = StringIO()
            quest_id_str = str(quest['Id'])
            if len (quest_id_str) == 6:
                stars = int(quest_id_str[-2:])
            else:
                stars = int(quest_id_str[-3:-1])
            star_emojis = ''
            for i in range(stars):
                if i < 5:
                    star_emojis += f'{await to_emoji(session, f"star1")} '
                else:
                    star_emojis += f'{await to_emoji(session, f"star2")} '
            quest_text.write(f'{star_emojis}\n')
            ic.add_items([schemas.ItemCount(**item) for item in quest['FixedBattleRewards']])
            quest_text.write(f'**Rewards:** {", ".join(await ic.get_total_strings())}\n')
            ic.clear()
            ic.add_items([schemas.ItemCount(**item) for item in quest['FirstBattleRewards']])
            quest_text.write(f'**First Time Rewards:** {", ".join(await ic.get_total_strings())}')
            ic.clear()
            container.add_item(ui.TextDisplay(quest_text.getvalue()))

    container.add_timestamp(data["timestamp"])
    return container

async def group_ui():
    container = MentemoriContainer('### Groups')
    resp = await api.fetch(
        api.MENTEMORI_GROUP_PATH,
        base_url=api.MENTEMORI_BASE_PATH
    )
    group_data = resp.json()

    server_groups = {Server(server): {} for server in Server}
    for group in group_data['data']:
        group_id = group['group_id']
        server, _ = from_world_id(group['worlds'][0])
        server_groups[server][group_id] = []
        for world_id in group['worlds']:
            _, world = from_world_id(world_id)
            server_groups[server][group_id].append(world)
    
    for server, group in server_groups.items():
        group_text = StringIO()
        group_text.write(f'**{server.name}**\n```\n')
        for group_id, worlds in sorted(group.items()):
            group_text.write(f'{group_id}: [{" ".join(map(str, worlds))}]\n')
        group_text.write('```\n')
        container.add_item(
            ui.TextDisplay(group_text.getvalue())
        )

    container.add_timestamp(group_data["timestamp"])
    return container

async def group_ranking_ui(server: Server, world: int) -> list[BaseContainer]:
    pages = []
    world_id = to_world_id(server, world)
    worlds = None

    # Find group for given world
    resp = await api.fetch(
        api.MENTEMORI_GROUP_PATH,
        base_url=api.MENTEMORI_BASE_PATH
    )
    group_data = resp.json()
    for group in group_data['data']:
        if world_id in group['worlds']:
            worlds = group['worlds']
            group_id = group['group_id']
            break
    
    if not worlds:
        raise BotError(f"Group for `{server.name} W{world}` was not found. Check if the server and world is correct.")

    ranking_data = await api.fetch_api(
        api.GUILD_RANKING_PATH,
        response_model=list[schemas.GuildRankInfo],
        query_params={'count': 200, 'world_id': worlds}
    )
    if len(ranking_data.data) == 0:
        raise BotError("No ranking data found.")

    rank = 1
    timestamp = ranking_data.data[0].timestamp
    for batch in batched(ranking_data.data, 50):
        container = MentemoriContainer(f'### Group Rankings [Group {group_id} | {server.name}]')
        rankings = []
        for guild in batch:
            rankings.append([rank, guild.world, f'{guild.bp:,}', guild.name])
            rank += 1
        container.add_item(
            ui.TextDisplay(f'```{make_table(rankings, ["No.", "World", "BP", "Name"], style="thin_compact", cell_padding=0)}```')
        ).add_timestamp(timestamp).add_ranking_update_footer()
        pages.append(container)

    return pages

def get_world_query(server: Server|None = None, world: int|None = None, world_ids: str|None = None, count: int = 500) -> tuple[dict, str]:
    '''Generate query parameters and text for rankings'''
    if world and not server:
        raise BotError("Cannot use `world` without `server`")
    text = 'All'
    params = {'count': count}

    if world_ids:
        try:
            world_ids = list(map(int, split(r'[,\s]+', world_ids.strip())))
            for world_id in world_ids:
                if not (1000 <= world_id <= 7000):  # Simple check for invalid world ids
                    raise ValueError()
        except ValueError:
            raise BotError(world_ids_help())
        text = ', '.join(map(str, world_ids))
        params['world_id'] = world_ids
    elif world:
        text = f'{server.name} {world}'
        params['world_id'] = to_world_id(server, world)
    elif server:
        text = server.name
        params['server'] = server

    return params, text

async def guild_ranking_ui(query_params, text)-> list[BaseContainer]:
    pages = []
    ranking_data = await api.fetch_api(
        api.GUILD_RANKING_PATH,
        response_model=list[schemas.GuildRankInfo],
        query_params=query_params
    )
    if len(ranking_data.data) == 0:
        raise BotError("No ranking data found.")

    rank = 1
    timestamp = ranking_data.data[0].timestamp
    for batch in batched(ranking_data.data, 50):
        container = MentemoriContainer(f'### Guild Rankings [{text}]')
        rankings = []
        for guild in batch:
            rankings.append([rank, guild.server, guild.world, f'{guild.bp:,}', guild.name])
            rank += 1
        table = make_table(rankings, ['No.', 'Server', 'World', 'BP',  'Name'], style='thin_compact', cell_padding=0)
        container.add_item(
            ui.TextDisplay(f'```{table}```')
        ).add_timestamp(timestamp).add_ranking_update_footer()
        pages.append(container)

    return pages

async def player_ranking_ui(params, text, category: PlayerCategory, show_all: bool) -> list[BaseContainer]:
    pages = []
    ranking_resp = await api.fetch_api(
        api.PLAYER_RANKING_PATH,
        response_model=list[schemas.PlayerRankInfo],
        query_params=params
    )
    ranking_data = ranking_resp.data
    if len(ranking_data) == 0:
        raise BotError("No ranking data found.")

    rank = 1
    timestamp = ranking_data[0].timestamp
    for batch in batched(ranking_data, 50):
        container = MentemoriContainer(f'### Player Rankings by {category.name} [{text}]')
        rankings = []
        for player in batch:
            if show_all:
                bp = f'{player.bp:,}'
                quest = from_quest_id(player.quest_id)
                rankings.append([rank, player.server, player.world, player.rank, quest, bp, player.name])
            else:
                if category == PlayerCategory.BP:
                    category_value = f'{player.bp:,}' if player.bp else 'N/A'
                elif category == PlayerCategory.Quest:
                    category_value = from_quest_id(player.quest_id)
                else:
                    category_value = player.rank
                rankings.append([rank, player.server, player.world, category_value, player.name])
            rank += 1
        if show_all:
            table = make_table(rankings, ['No.', 'Server', 'World', 'Rank', 'Quest', 'BP', 'Name'], style='thin_compact', cell_padding=0)
        else:
            table = make_table(rankings, ['No.', 'Server', 'World', category.name, 'Name'], style='thin_compact', cell_padding=0)
        container.add_item(
            ui.TextDisplay(f'```{table}```')
        ).add_timestamp(timestamp).add_ranking_update_footer()
        pages.append(container)

    return pages

async def tower_ranking_ui(params: dict, text: str, category: TowerCategory) -> list[BaseContainer]:
    pages = []
    ranking_resp = await api.fetch_api(
        api.PLAYER_RANKING_PATH,
        response_model=list[schemas.PlayerRankInfo],
        query_params=params
    )
    ranking_data = ranking_resp.data
    if len(ranking_data) == 0:
        raise BotError("No ranking data found.")

    rank = 1
    timestamp = ranking_data[0].timestamp
    for batch in batched(ranking_data, 50):
        container = MentemoriContainer(f'### Player Rankings by {category.name} [{text}]')
        rankings = []
        for player in batch:
            rankings.append([rank, player.server, player.world, getattr(player, f'{category.value}_id'), player.name])
            rank += 1
        table = make_table(rankings, ['Rank', 'Server', 'World', 'Floor',  'Name'], style='thin_compact', cell_padding=0)
        container.add_item(
            ui.TextDisplay(f'```{table}```')
        ).add_timestamp(timestamp).add_ranking_update_footer()
        pages.append(container)
    return pages

async def gacha_option_map(server: Server) -> dict:
    content = {
        GachaLog.IoC.name: partial(gacha_ui, gacha=GachaLog.IoC, server=server),
        GachaLog.IoSG.name: partial(gacha_ui, gacha=GachaLog.IoSG, server=server)
    }
    return content

async def gacha_ui(gacha: GachaLog, server: Server, language: Language) -> list[BaseContainer]:
    pages = []
    for server_id in game_server[server]:
        container = MentemoriContainer(f'### {gacha.name} [{server_id}]')
        resp = await api.fetch(
            api.MENTEMORI_GACHA_PATH.format(server_id=server_id, gacha=gacha.value),
            base_url=api.MENTEMORI_BASE_PATH
        )
        data = resp.json()

        prev_player = None
        for player in data['data']:
            if prev_player and prev_player != player['Name']:
                container.add_item(ui.Separator())
            itemcount = schemas.ItemCount(**player['UserItem'])
            if itemcount.item_type == ItemType.Character:
                result = await character_string(itemcount.item_id, language)
            else:  # Diamonds
                result = await item_count_string(itemcount, language=language)
            container.add_item(ui.TextDisplay(f'**Player:** {player['Name']}\n{result}'))
            prev_player = player['Name']
        container.add_timestamp(data['timestamp'])
        pages.append(container)
    return pages

async def raid_ranking_ui(server: Server|None=None) -> BaseContainer|None:
    pages = []
    resp = await api.fetch(
        api.MENTEMORI_RAID_EVENT_PATH.format(world_id=f'{server}000' if server else 0),
        base_url=api.MENTEMORI_BASE_PATH
    )
    data: list[dict] = resp.json()['data']
    data.sort(key=lambda x: x['damage'], reverse=True)
    
    if data[0]['damage'] == 0:
        return BaseContainer('No guild raid event is currently active.')
    
    for batch in batched(data, 50):
        container = MentemoriContainer('### Guild Raid Rankings')
        rankings = []
        for world_data in batch:
            server, world = from_world_id(world_data['world_id'])
            rankings.append([server, world, f'{world_data['damage']:,}'])

        table = make_table(rankings, ['Server', 'World', 'Damage'], style='thin_compact', cell_padding=0)
        container.add_item(ui.TextDisplay(f'```{table}```'))
        pages.append(container)
    return pages
