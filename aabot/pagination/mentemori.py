from enum import Enum
from io import StringIO
from itertools import batched

from discord import Color, Embed, Interaction
from table2ascii import table2ascii as t2a, Alignment, PresetStyle

from aabot.pagination.views import ButtonView
from aabot.utils import api
from aabot.utils.utils import from_world_id, from_quest_id, character_title
from common import schemas
from common.enums import Server, Language

def make_table(data, header: list[str]):
    return t2a(
        header=header,
        body=data,
        style=PresetStyle.thin_compact,
        alignments=Alignment.LEFT,
        cell_padding=0
    )

temple_type = {
    1: 'Green Orb',
    2: 'Water',
    3: 'Red Potion',
    4: 'Red Orbs',
    5: 'Rune Tickets'
}

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

def temple_embed(data, server: Server, world: int):
    description = StringIO()
    quest_ids = data['data']['quest_ids']
    # world_id = data['data']['world_id']
    
    if len(str(quest_ids[0])) != 6:
        description.write(f"Temple event is ongoing")
    else:
        description.write(f'Lv. {int(str(quest_ids[0])[1:4])}\n\n')
        for quest in quest_ids:
            quest_id_str = str(quest)
            description.write(f'**{int(quest_id_str[-2:])} Star: {temple_type.get(int(quest_id_str[0]))}**\n')
    time = str(data["timestamp"])
    description.write(f'\nLast Update: <t:{time}:R>')

    return Embed(
        title=f'Temple {server.name} W{world}',
        description=description.getvalue(),
        color=Color.yellow()
    ).set_footer(text='Reward details cannot be provided since they have been removed from the client data.')

def group_embed(group_data):
    description = StringIO()

    server_groups = {Server(server): {} for server in Server}
    for group in group_data['data']:
        group_id = group['group_id']
        server, _ = from_world_id(group['worlds'][0])
        server_groups[server][group_id] = []
        for world_id in group['worlds']:
            _, world = from_world_id(world_id)
            server_groups[server][group_id].append(world)
    
    for server, group in server_groups.items():
        description.write(f'**{server.name}**\n```\n')
        for group_id, worlds in sorted(group.items()):
            description.write(f'{group_id}: [{" ".join(map(str, worlds))}]\n')
        description.write('```\n')
    
    return Embed(title="Groups", description=description.getvalue(), color=Color.blue())

def group_ranking_view(interaction: Interaction, ranking_data: schemas.APIResponse[list[schemas.GuildRankInfo]], server: Server, group: int):
    embed_dict = {'default': []}
    rank = 1
    for batch in batched(ranking_data.data, 50):
        rankings = []
        for guild in batch:
            rankings.append([rank, guild.world, f'{guild.bp:,}', guild.name])
            rank += 1
        table = make_table(rankings, ['Rank','World', 'BP', 'Name'])

        embed_dict['default'].append(
            Embed(
                title=f'Group Rankings [Group {group} | {server.name}]',
                description=f'```{table}```',
                color=Color.orange()
            )
        )

    return ButtonView(interaction.user, embed_dict)

def guild_ranking_view(
    interaction: Interaction,
    ranking_data: schemas.APIResponse[list[schemas.GuildRankInfo]],
    filter_text: str
    ) -> ButtonView:
    embed_dict = {'default': []}
    rank = 1
    for batch in batched(ranking_data.data, 50):
        rankings = []
        for guild in batch:
            rankings.append([rank, guild.server, guild.world, f'{guild.bp:,}', guild.name])
            rank += 1
        table = make_table(rankings, ['Rank', 'Server', 'World', 'BP',  'Name'])

        embed_dict['default'].append(
            Embed(
                title=f'Guild Rankings [{filter_text}]',
                description=f'```{table}```',
                color=Color.orange()
            )
        )

    return ButtonView(interaction.user, embed_dict)

class PlayerCategory(Enum):
    BP = 'bp'
    Quest = 'quest'
    Rank = 'rank'

def player_ranking_view(
    interaction: Interaction,
    ranking_data: schemas.APIResponse[list[schemas.PlayerRankInfo]],
    category: PlayerCategory,
    filter_text: str,
    show_all: bool
    ) -> ButtonView:
    embed_dict = {'default': []}
    rank = 1
    test = 0
    for batch in batched(ranking_data.data, 50):
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
            table = make_table(rankings, ['No.', 'Server', 'World', 'Rank', 'Quest', 'BP', 'Name'])
        else:
            table = make_table(rankings, ['Rank', 'Server', 'World', category.name, 'Name'])
        embed_dict['default'].append(
            Embed(
                title=f'Player Rankings by {category.name} [{filter_text}]',
                description=f'```{table}```',
                color=Color.orange()
            )
        )

    return ButtonView(interaction.user, embed_dict)

class TowerCategory(Enum):
    Infinity = 'tower'
    Azure = 'azure_tower'
    Crimson = 'crimson_tower'
    Emerald = 'emerald_tower'
    Amber = 'amber_tower'

def tower_ranking_view(
    interaction: Interaction,
    ranking_data: schemas.APIResponse[list[schemas.PlayerRankInfo]],
    category: PlayerCategory,
    filter_text: str
):
    embed_dict = {'default': []}
    rank = 1
    for batch in batched(ranking_data.data, 50):
        rankings = []
        for player in batch:
            rankings.append([rank, player.server, player.world, getattr(player, f'{category.value}_id'), player.name])  # actual attribute are [tower]_id
            rank += 1
        table = make_table(rankings, ['Rank', 'Server', 'World', 'Floor',  'Name'])
        
        embed = Embed(
            title=f'{category.name} Tower Rankings [{filter_text}]',
            description=f'```{table}```',
            color=Color.orange()
        )
        if category != TowerCategory.Infinity:
            embed.set_footer(text=f"Note that ranking data for elemental towers is collected from only the top 20 of each world.")
        embed_dict['default'].append(embed)
        
    return ButtonView(interaction.user, embed_dict)


class GachaLog(Enum):
    IoC = 'destiny_log'
    IoSG = 'stars_guidance_log'

game_server = {
    1: ['jp1', 'jp2', 'jp3', 'jp4', 'jp5'],
    2: ['kr1', 'kr2'],
    3: ['ap1', 'ap2'],
    4: ['us1'],
    5: ['eu1'],
    6: ['gl1', 'gl2']
}

async def gacha_view(interaction: Interaction, gacha: GachaLog, server: Server, language: Language):
    embed_dict = {'default': []}
    item_cache = {}

    for server_id in game_server[server]:
        description = StringIO()
        resp = await api.fetch(
            api.MENTEMORI_GACHA_PATH.format(server_id=server_id, gacha=gacha.value),
            base_url=api.MENTEMORI_BASE_PATH
        )
        data = resp.json()

        for player in data['data']:
            item_type = player['UserItem']['ItemType']
            item_id = player['UserItem']['ItemId']

            if (item_id, item_type) not in item_cache:
                item_resp = await api.fetch_item(item_id, item_type, language=language)
                item = item_resp.data
                item_cache[(item_id, item_type)] = item
            else:
                item = item_cache[(item_id, item_type)]

            if isinstance(item, schemas.CharacterItem):
                result = f'**Character:** {character_title(item.title, item.name)}'
            else:  # Diamonds
                result = f'**__30,000x {item.name}__**'
                
            description.write(
                f"**Player:** {player['Name']}\n"
                f"{result}\n\n"
            )
        description.write(f'Last Updated: <t:{data['timestamp']}:R>')
        embed_dict['default'].append(
            Embed(
                title=f'{gacha.name} [{server_id}]',
                description=description.getvalue()
            )
        )
    return ButtonView(interaction.user, embed_dict)