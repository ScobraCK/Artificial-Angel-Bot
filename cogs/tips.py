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
        awakening = 'https://cdn.discordapp.com/attachments/1032035546412875817/1033509806109102120/unknown-13.png'
        embed.set_image(url=awakening)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def soul_affinity(self, interaction: discord.Interaction):
        '''Soul affinity chart'''
        embed=discord.Embed()
        affinity = 'https://cdn.discordapp.com/attachments/1032035546412875817/1032035874982084708/20221018_135122.jpg'
        embed.set_image(url=affinity)
        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
	await bot.add_cog(Tips(bot))