import discord
from discord import app_commands
from discord.ext import commands

import common

class Tips(commands.Cog):
    '''These are helpful tip commands'''

    def __init__(self, bot):
        self.bot = bot
    
    
    @app_commands.command()
    async def awakening(self, interaction: discord.Interaction):
        '''Awakening cost chart'''
        embed=discord.Embed()
        awakening = common.raw_asset_link_header + 'Bot/awakening_costs.png'
        embed.set_image(url=awakening)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def soul_affinity(self, interaction: discord.Interaction):
        '''Soul affinity chart'''
        embed=discord.Embed()
        affinity = common.raw_asset_link_header + 'Bot/soul_affinity.jpg'
        embed.set_image(url=affinity)
        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
	await bot.add_cog(Tips(bot))