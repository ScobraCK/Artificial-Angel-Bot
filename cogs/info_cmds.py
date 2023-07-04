import discord
from discord import app_commands
from discord.ext import commands

import requests, json
from enum import Enum
from my_view import Button_View
from dataclasses import dataclass
from typing import List
from dacite import from_dict
from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from io import StringIO


# testing database ################################### (temp)
import sqlite3

class GuildDB():
    def __init__(self) -> None:
        self.con = sqlite3.connect('guild.db')
        self.cur = self.con.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            id varchar(12) PRIMARY KEY,
            name text,
            bp int,
            level int,
            world int,
            server int)
        """)

    def insert_guilds(self, guilds: dict, server: int, world: int, ):
        for guild in guilds:
            guild['world'] = world
            guild['server'] = server
            self.cur.execute("INSERT OR REPLACE INTO guilds (id, name, bp, level, world, server)"
                             "VALUES (:id, :name, :bp, :level, :world, :server)",
                             guild)
        self.con.commit()

    def get_server_ranking(self, server):
        res = self.cur.execute(
            "SELECT bp, world, name FROM guilds WHERE server = (?) ORDER BY bp DESC", (server, )
        )
        return res.fetchmany(200)
    
    def close(self):
        self.con.close()

def fetch_guildlist(server: int, world: int):
    world_id = f"{server}{world:03}"
    url = f"https://api.mentemori.icu/{world_id}/guild_ranking/latest"
    resp = requests.get(url)
    data = json.loads(resp.content.decode('utf-8'))

    return data


##################################################

class Region(Enum): #temp solution
    JP = 1
    KR = 2
    AP = 3
    NA = 4
    EU = 5
    GL = 6

temple_type = {
    1: 'Green Orb',
    2: 'Water',
    3: 'Red Potion',
    4: 'Red Orbs',
    5: 'Rune Tickets'
}

@dataclass
class GuildData():
    world: int
    bp: int
    name: str
    level: int

    def list_bp(self):
        return [self.bp, self.world, self.name]

def guildlist_to_ascii(guild_list: List[dict], start: int=1):
    ranking = []
    for rank, guild in enumerate(guild_list, start):
        ranking.append([rank] + list(guild))

    output = t2a(
        header=["Rank", "BP", "World", "Name",],
        body=ranking,
        style=PresetStyle.thin_compact
    )
    return output

# async def world_autocomplete(
#     interaction: discord.Interaction, 
#     current: str) -> List[app_commands.Choice[int]]:
#     worlds = region_map.get(interaction.namespace.server)
#     worlds_str = [str(world) for world in worlds]
#     return [
#         app_commands.Choice(name=choice, value=int(choice))
#         for choice in worlds_str if choice.startswith(current)
#     ]


class Info(commands.Cog, name='Info Commands'):
    '''Commands that fetch ingame info'''

    def __init__(self, bot):
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

            text = f'Lv. {int(str(quest_ids[0])[1:4])}\n\n'
            for quest in quest_ids:
                quest_id_str = str(quest)
                text += f'**{int(quest_id_str[-2:])} Star: {temple_type.get(int(quest_id_str[0]))}**\n'

            time = str(data["timestamp"])
            text += f'\nLast update: <t:{time}:R>'
            embed.description = text

            embed.set_footer(text='Prototype command')
            await interaction.response.send_message(
                embed=embed
            )

    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in'
    )
    async def guildrankings(self, interaction: discord.Interaction, server: Region):
        '''Guild rankings prototype'''

        if self.bot.block_guilddb:
            await interaction.response.send_message(message='Updating data, please try again in a short while.', ephemeral=True) 

        else:
            db = GuildDB()
            sorted_guildlist = db.get_server_ranking(server.value)
            db.close()

            embeds = []
            for i in range(0, 200, 50):  # top 100
                if server == Region.EU and i > 100:
                    break

                text = f'```{guildlist_to_ascii(sorted_guildlist[i:i+50], i+1)}```'
                embed = discord.Embed(
                    title=f'Top 100 Guild Rankings by BP({server.name})',
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
    async def checktemple(self, interaction: discord.Interaction):
        '''Shows which worlds have /temple command available'''

        url = f"https://api.mentemori.icu/worlds"
        resp = requests.get(url)
        data = json.loads(resp.text)
        worlds = data['data']

        text = StringIO()
        
        current_server = ''
        for world in worlds:
            if world['server'] != current_server:
                current_server = world['server']             
                text.write(f'\n**{current_server.upper()}: **')
            id = int(str(world['world_id'])[-2:])
            if world['temple']:
                text.write(f' {id}')

        embed = discord.Embed(
            title='Worlds with temple command unlocked',
            colour=discord.Colour.orange(),
            description=text.getvalue()
        )

        embed.set_footer(text=(
            'Due to current code, the world may be listed here but not shown as an option. ' 
            'Ignore the option choice and input the world in this case. '
            'Regard the worlds listed here as most up-to-date.'
        ))

        await interaction.response.send_message(embed=embed)


async def setup(bot):
	await bot.add_cog(Info(bot))
        

if __name__ == "__main__":
    from pprint import pprint
    pprint(fetch_guildlist(11))