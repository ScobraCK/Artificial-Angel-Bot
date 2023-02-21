import discord
from discord import app_commands
from discord.ext import commands

import common

class Tips(commands.Cog, name='Other Commands'):
    '''These are helpful tip commands'''

    def __init__(self, bot):
        self.bot = bot
    
    
    @app_commands.command()
    async def awakening(self, interaction: discord.Interaction):
        '''Awakening cost chart'''
        embed=discord.Embed()
        img = common.raw_asset_link_header + 'Bot/awakening_costs.png'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def soulaffinity(self, interaction: discord.Interaction):
        '''Soul affinity chart'''
        embed=discord.Embed()
        img = common.raw_asset_link_header + 'Bot/soul_affinity.jpg'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def enhancecost(self, interaction: discord.Interaction):
        '''Equipment enhancement cost chart'''
        embed=discord.Embed()
        img = common.raw_asset_link_header + 'Bot/enhance.png'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def seteffect(self, interaction: discord.Interaction):
        '''Equipment set effect chart'''
        embed=discord.Embed()
        img = common.raw_asset_link_header + 'Bot/seteffects.png'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
	await bot.add_cog(Tips(bot))