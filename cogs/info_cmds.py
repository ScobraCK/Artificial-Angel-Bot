from dataclasses import dataclass
from typing import List
from dacite import from_dict
from table2ascii import table2ascii as t2a, PresetStyle, Alignment
import discord
from discord import app_commands
from discord.ext import commands

import requests, json
from enum import Enum
from my_view import Button_View

class Region(Enum): #temp solution
    JP = 1
    NA = 4
    EU = 5

na_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
jp_list = [5, 12, 18, 47, 54, 55, 57, 63, 72, 75, 76]
eu_list = [1, 2, 3, 4, 5, 6]

region_map = {
    1: jp_list,
    4: na_list,
    5: eu_list
}

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
        return [self.bp, self.world,self.name]

def fetch_guildlist(server: int, world: int):
    world_id = f"{server}{world:03}"
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
        header=["Rank", "BP", "World", "Name",],
        body=ranking,
        style=PresetStyle.thin_compact
    )
    return output

async def world_autocomplete(
    interaction: discord.Interaction, 
    current: str) -> List[app_commands.Choice[int]]:
    worlds = region_map.get(interaction.namespace.server)
    worlds_str = [str(world) for world in worlds]
    return [
        app_commands.Choice(name=choice, value=int(choice))
        for choice in worlds_str if choice.startswith(current)
    ]


class Info(commands.Cog, name='Info Commands'):
    '''Commands that fetch ingame info'''

    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
    )
    @app_commands.autocomplete(world=world_autocomplete)
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
                'The current world may not be supported for this command. '
                'Contact Scobra#7120 or ping @Scobra in the MementoMori Unofficial discord for more details.',
                ephemeral=True
            )
        else:
            quest_ids = data['data']['quest_ids']

            text = f'Lv. {int(str(quest_ids[0])[1:4])}\n\n'
            for quest in quest_ids:
                quest_id_str = str(quest)
                text += f'**{int(quest_id_str[-2:])} Star: {temple_type.get(int(quest_id_str[0]))}**\n'

            embed.description = text

            embed.set_footer(text='Prototype command')
            await interaction.response.send_message(
                embed=embed
            )

    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
    )
    async def guildrankings(self, interaction: discord.Interaction, server: Region):
        '''Guild rankings prototype'''

        await interaction.response.defer()

        guildlist = []
        world_list = region_map.get(server.value)
        for world in world_list:
            guildlist += fetch_guildlist(server.value, world)
        sorted_guildlist = sorted(guildlist, key=lambda x: x.bp, reverse=True)

        embeds = []

        for i in range(0, 100, 50):  # top 100
            text = f'```{guildlist_to_ascii(sorted_guildlist[i:i+50], i+1)}```'
            embed = discord.Embed(
                title=f'Top 100 Guild Rankings by BP({server.name})',
                description=text
            )
            embed.set_footer(text=f'Only contains {server.name} worlds {str(world_list)}')
            embeds.append(embed)

        user = interaction.user
        view = Button_View(user, embeds)
        await view.btn_update()

        await interaction.followup.send(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Info(bot))
        

if __name__ == "__main__":
    from pprint import pprint
    pprint(fetch_guildlist(11))