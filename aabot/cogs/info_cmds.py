import discord
from discord import app_commands
from discord.ext import commands

import requests, json
from enum import Enum
from my_view import Button_View
from typing import List, Optional
from dacite import from_dict
from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from io import StringIO
import aiohttp

from mementodb import fetch_group_list
from main import AABot
from quests import convert_to_stage
from common import Tower, Language
from character import get_full_name

class Region(Enum): #temp solution
    JP = 1
    KR = 2
    AP = 3
    NA = 4
    EU = 5
    GL = 6

class RankingType(Enum):
    BP = 'bp'
    # Rank = 'rank'
    Quest = 'quest_id'
    # Tower = 'tower'

temple_type = {
    1: 'Green Orb',
    2: 'Water',
    3: 'Red Potion',
    4: 'Red Orbs',
    5: 'Rune Tickets'
}

# move out of cog later
class GachaLog(Enum):
    IoC = 'destiny_log'
    IoSG = 'stars_guidance_log'

class IoCServer(Enum):
    JP = ['jp1', 'jp2', 'jp3', 'jp4', 'jp5']
    KR = ['kr1', 'kr2']
    AP = ['ap1', 'ap2']
    NA = ['us1']
    EU = ['eu1']
    GL = ['gl1', 'gl2']

def guildlist_to_ascii(guild_list: List[dict], start: int=1):
    ranking = []
    for rank, guild in enumerate(guild_list, start):
        guild_data = [rank] + list(guild)
        guild_data[1] = f'{guild_data[1]:,}'  # BP
        ranking.append(guild_data)

    output = t2a(
        header=["Rank", "BP", "World", "Name",],
        body=ranking,
        style=PresetStyle.thin_compact,
        alignments=Alignment.LEFT
    )
    return output

def towerlist_to_ascii(players: List[dict], start: int=1, server=None):
    ranking = []
    if server:
        for rank, player in enumerate(players, start):
            playerdata = [rank] + list(player)
            ranking.append(playerdata)
        
        output = t2a(
            header=["Rank", "World", 'Floor', "Name"],
            body=ranking,
            style=PresetStyle.thin_compact,
            alignments=Alignment.LEFT
        )

    else:
        for rank, player in enumerate(players, start):
            playerdata = [rank] + list(player)
            # server
            playerdata[1] = Region(playerdata[1]).name
            ranking.append(playerdata)
        
        output = t2a(
            header=["Rank", 'Server', "World", 'Floor', "Name"],
            body=ranking,
            style=PresetStyle.thin_compact,
            alignments=Alignment.LEFT
        )
    return output

def playerlist_to_ascii(players: List[dict], start: int=1, server=None):
    ranking = []
    if server:
        for rank, player in enumerate(players, start):
            playerdata = [rank] + list(player)
            playerdata[2] = (f'{playerdata[2]:,}' if isinstance(playerdata[2], int) else playerdata[2])  # BP
            # quest
            if quest_id := playerdata[-2]:
                playerdata[-2] = convert_to_stage(quest_id) if quest_id else None  
            ranking.append(playerdata)
        
        output = t2a(
            header=["Rank", "World", 'BP', 'Quest', "Name"],
            body=ranking,
            style=PresetStyle.thin_compact,
            alignments=Alignment.LEFT
        )

    else:
        for rank, player in enumerate(players, start):
            playerdata = [rank] + list(player)
            playerdata[3] = (f'{playerdata[3]:,}' if isinstance(playerdata[3], int) else playerdata[3])   # BP
            # server
            playerdata[1] = Region(playerdata[1]).name
            # quest
            if quest_id := playerdata[-2]:
                playerdata[-2] = convert_to_stage(quest_id) if quest_id else None  
            ranking.append(playerdata)
        
        output = t2a(
            header=["Rank", 'Server', "World", 'BP', 'Quest', "Name"],
            body=ranking,
            style=PresetStyle.thin_compact,
            alignments=Alignment.LEFT
        )
    return output

def in_range(num, start, end):
    if num == '':
        return True
    num = int(num)
    if start <= num <= end:
        return True
    if (start//10) <= num <= (end//10):
        return True
    if (start//100) <= num <= (end//100):
        return True
    return False

async def group_autocomplete(
        interaction: discord.Interaction, 
        current: str) -> List[app_commands.Choice[str]]:
    group_list = fetch_group_list(interaction.namespace.server)  # [(id, start, end), ...]

    return [
        app_commands.Choice(name=f'{choice[1]}-{choice[2]}', value=f'{choice[1]}-{choice[2]}')
        for choice in group_list if in_range(current, choice[1], choice[2])
    ]

# IoC
def ioc_embed(data, title, md, lang):
    description = StringIO()
    for player in data:
        description.write(
            f"**Player:** {player['Name']}\n"
            f"**Character:** {get_full_name(player['UserItem']['ItemId'], md, lang)}\n\n"
        )
    
    embed = discord.Embed(
        title=title,
        description=description.getvalue()
    )
    
    return embed

class Info(commands.Cog, name='Info Commands'):
    '''Commands that fetch ingame info'''

    def __init__(self, bot: AABot):
        self.bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
    )
    async def temple(self, interaction: discord.Interaction,
                     server: Region,
                     world: int):
        '''View Temple prototype'''
        
        embed=discord.Embed(
                title=f'Temple {server.name} W{world}'
        )
        world_id = f"{server.value}{world:03}"
        url = f"https://api.mentemori.icu/{world_id}/temple/latest"
        resp = requests.get(url)
        data = json.loads(resp.text)

        if data['status'] == 404:
            await interaction.response.send_message(
                f'{server.name} {world}: World not found',
                ephemeral=True
            )
        else:
            quest_ids = data['data']['quest_ids']
            if len(str(quest_ids[0])) != 6:
                text = f"Events are not supported yet. Sorry."
            else:
                text = f'Lv. {int(str(quest_ids[0])[1:4])}\n\n'
                for quest in quest_ids:
                    quest_id_str = str(quest)
                    text += f'**{int(quest_id_str[-2:])} Star: {temple_type.get(int(quest_id_str[0]))}**\n'

            time = str(data["timestamp"])
            text += f'\nLast Update: <t:{time}:R>'
            embed.description = text

            embed.set_footer(text='Prototype command')
            await interaction.response.send_message(
                embed=embed
            )

    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
        group='The group your world is in'
    )
    @app_commands.autocomplete(group=group_autocomplete)
    async def grouprankings(self, 
                            interaction: discord.Interaction, 
                            server: Region,
                            group: str):
        '''Guild rankings by group'''
        if group.isnumeric():
            group_id = self.bot.db.get_group_id(server.value, int(group))
        else:
            group_id = self.bot.db.get_group_id(server.value, int(group.split('-')[0]))

        if group_id is None:
            await interaction.response.send_message(
                f"Group Id of `{group}` on server `{server.name}` was not found",
                ephemeral=True
            )
        else:
            group_id = group_id[0]
            rankings = self.bot.db.get_group_guild_ranking(server.value, group_id)
            start, end = self.bot.db.get_group_worlds(group_id)
            last_update = self.bot.db.get_last_update_guild()
            embed = discord.Embed(
                    title=f'Guild Rankings ({server.name} {start}-{end})',
                    description=f'```{guildlist_to_ascii(rankings)}```\nLast Updated: <t:{last_update}>',
                    colour=discord.Colour.orange()
                )
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server='The region your world is in')
    async def guildrankings(self, interaction: discord.Interaction, server: Region):
        '''Guild rankings prototype'''
    
        sorted_guildlist = self.bot.db.get_server_guild_ranking(server.value)
        last_update = self.bot.db.get_last_update_guild()
        
        embeds = []
        for i in range(0, 200, 50):  # top 100
            if server == Region.EU and i > 100:
                break

            text = f'```{guildlist_to_ascii(sorted_guildlist[i:i+50], i+1)}```\nLast Updated: <t:{last_update}>'
            embed = discord.Embed(
                title=f'Top Guild Rankings by BP ({server.name})',
                description=text,
                colour=discord.Colour.orange()
            )
            embeds.append(embed)

        user = interaction.user
        view = Button_View(user, embeds)
        await view.btn_update()

        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message

    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in. Leave empty for all servers',
        category='The ranking category. Default BP')
    async def playerrankings(self, 
                             interaction: discord.Interaction, 
                             server: Optional[Region],
                             category: Optional[RankingType] = RankingType.BP):
        '''Player rankings for server'''
        
        if server:
            players = self.bot.db.get_server_player_ranking(server.value, category.value)
            servername = server.name
        else:
            players = self.bot.db.get_all_player_ranking(category.value)
            servername = 'All Servers'
        last_update = self.bot.db.get_last_update_player()
        
        embeds = []
        for i in range(0, len(players), 50):  # top 100
            if i+50 > len(players):
                break

            text = f'```{playerlist_to_ascii(players[i:i+50], i+1, server)}```\nLast Updated: <t:{last_update}>'
            embed = discord.Embed(
                title=f'Top Player Rankings by {category.name} ({servername})',
                description=text,
                colour=discord.Colour.orange()
            )
            embeds.append(embed)

        user = interaction.user
        view = Button_View(user, embeds)
        await view.btn_update()

        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message
        
    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in. Leave empty for all servers',
        towertype="The tower type. Defaults to the Tower of Infinity")
    async def towerrankings(self, 
                             interaction: discord.Interaction, 
                             server: Optional[Region],
                             towertype: Optional[Tower]=Tower.Infinity):
        '''Tower rankings'''
        
        if server:
            players = self.bot.db.get_server_tower_ranking(server.value, towertype)
            servername = server.name
        else:
            players = self.bot.db.get_all_tower_ranking(towertype, count=500)
            servername = 'All Servers'
        
        last_update = self.bot.db.get_last_update_player()
            
        embeds = []
        for i in range(0, len(players), 50):
            if i+50 > len(players):
                break

            text = f'```{towerlist_to_ascii(players[i:i+50], i+1, server)}```\nLast Updated: <t:{last_update}>'
            embed = discord.Embed(
                title=f'Top {towertype.name} Tower Rankings ({servername})',
                description=text,
                colour=discord.Colour.orange()
            )
            
            if towertype != Tower.Infinity:
                embed.set_footer(text=f"Note that ranking data for elemental towers is collected from only the top 20 of each world.")
            embeds.append(embed)

        user = interaction.user
        view = Button_View(user, embeds)
        await view.btn_update()

        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message

    @app_commands.command()
    async def checktemple(self, interaction: discord.Interaction):
        '''Shows which worlds have /temple command available'''

        url = f"https://api.mentemori.icu/worlds"
        resp = requests.get(url)
        data = json.loads(resp.text)
        worlds = sorted(data['data'], key=lambda x: x['world_id'])

        text = StringIO()
        
        current_server = ''
        for world in worlds:
            if world['server'] != current_server:
                current_server = world['server']             
                text.write(f'\n**{current_server.upper()}: **')
            id = int(str(world['world_id'])[-3:])  # world_id
            if world['temple']:
                text.write(f' {id}')

        embed = discord.Embed(
            title='Worlds with temple command unlocked',
            colour=discord.Colour.orange(),
            description=text.getvalue()
        )

        await interaction.response.send_message(embed=embed)
        
    @app_commands.command()
    @app_commands.describe(
        gacha='Invocation of Chance (IoC) / Invocation of Stars Guidance (IoSG)',
        server='Server to check IoC',
        language='Text language. Defaults to English.'
    )
    async def gachalogs(
        self, 
        interaction: discord.Interaction, 
        gacha: GachaLog,
        server: IoCServer,
        language: Optional[Language]=Language.EnUs):
        '''Shows IoC or IoSG logs'''

        await interaction.response.defer()
        embeds = []
        for server_id in server.value:
            async with aiohttp.ClientSession() as session:
                url = f'https://api.mentemori.icu/{server_id}/{gacha.value}/latest'
                async with session.get(url) as resp:
                    data = await resp.json()
                    if data['status'] != 200:
                        await interaction.response.send_message('Something went wrong', ephemeral=True)
                    title = f'{gacha.name} - {server_id.upper()}'
                    embeds.append(ioc_embed(data['data'], title, self.bot.masterdata, language))
 
        user = interaction.user
        view = Button_View(user, embeds)
        await view.btn_update()
        
        await interaction.followup.send(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Info(bot))
        