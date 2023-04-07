from dataclasses import dataclass
from typing import List
from dacite import from_dict
from table2ascii import table2ascii as t2a, PresetStyle
import discord
from discord import app_commands
from discord.ext import commands

import requests, json
from enum import Enum
from my_view import Button_View

class Region(Enum): #temp solution
    JP = 1
    NA = 4

na_list = [1, 2, 3, 4, 5, 6, 10, 11, 12]

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
    stock: int

    def list_bp(self):
        return [self.name, self.bp, self.world]

def fetch_guildlist(world: int):
    world_id = f"4{world:03}"
    url = f"https://api.mentemori.icu/{world_id}/guild_ranking/latest"
    resp = requests.get(url)
    data = json.loads(resp.content.decode('utf-8'))
    guilds = []
    for guild_data in data['data']['rankings']['bp']:
        guild_data['world'] = world
        guild = from_dict(data_class=GuildData, data=guild_data)
        guilds.append(guild)
    return guilds

def guildlist_to_ascii(guild_list: List[GuildData], start: int=1):
    ranking = []
    for rank, guild in enumerate(guild_list, start):
        ranking.append([rank] + guild.list_bp())

    output = t2a(
        header=["Rank", "Name", "BP", "World"],
        body=ranking,
        style=PresetStyle.thin_compact
    )
    return output

class Info(commands.Cog, name='Info Commands'):
    '''Commands that fetch ingame info'''

    def __init__(self, bot):
        self.bot = bot
    
    
    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
        world='The world number in the server (only supports JP-72, NA-1,2,3,4,5,6,10,11,12 currently)'
    )
    async def temple(self, interaction: discord.Interaction,
                     server: Region,
                     world: int):
        '''View Temple prototype'''
        
        if world not in [1, 2, 3, 4, 5, 6, 10, 11, 12, 72]:
            await interaction.response.send_message(
                "The current world is not supported."
                "Contact Scobra#7120 for more info if you wish to help add your world."
            )
        else:
            embed=discord.Embed(
                 title='Temple (Prototype command)'
            )
            world_id = f"{server.value}{world:03}"
            url = f"https://api.mentemori.icu/{world_id}/temple/latest"
            resp = requests.get(url)
            data = json.loads(resp.text)
            quest_ids = data['data']['quest_ids']

            text = f'Lv. {int(str(quest_ids[0])[1:4])}\n\n'
            for quest in quest_ids:
                quest_id_str = str(quest)
                text += f'**{int(quest_id_str[-2:])} Star: {temple_type.get(int(quest_id_str[0]))}**\n'

            embed.description = text
            await interaction.response.send_message(
                embed=embed
            )

    @app_commands.command()
    async def guildrankings(self, interaction: discord.Interaction):
        '''Guild rankings prototype'''
        guildlist = []
        for world in na_list:
            guildlist += fetch_guildlist(world)
        sorted_guildlist = sorted(guildlist, key=lambda x: x.bp, reverse=True)

        text1 = f'```{guildlist_to_ascii(sorted_guildlist[:50])}```'
        embed1 = discord.Embed(
            title='Top 100 Guild Rankings by BP',
            description=text1
        )
        embed1.set_footer(text='Only contains NA world 1-6, 10-12')

        text2 = f'```{guildlist_to_ascii(sorted_guildlist[50:100], 51)}```'
        embed2 = discord.Embed(
            title='Top 100 Guild Rankings by BP',
            description=text2
        )
        embed2.set_footer(text='Only contains NA world 1-6, 10-12')

        user = interaction.user
        view = Button_View(user, [embed1, embed2])
        await view.btn_update()

        await interaction.response.send_message(embed=embed1, view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Info(bot))
        

if __name__ == "__main__":
    from pprint import pprint
    pprint(fetch_guildlist(11))