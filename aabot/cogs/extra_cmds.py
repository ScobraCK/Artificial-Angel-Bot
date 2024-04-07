import discord
from discord import app_commands
from discord.ext import commands



class Extras(commands.Cog, name='Extra Commands'):
    '''Extra commands not in any category'''

    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command()
    async def changelog(self, interaction: discord.Interaction):
        '''
        Shows Changelog
        To be adjusted as the changelog gets larger
        '''
        embed=discord.Embed(title='Changelog')
        text='```json\n'
        with open('changelog.txt', 'r') as f:
            for line in f:
                text+=line
        text+='```'
        embed.description = text      
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
	await bot.add_cog(Extras(bot))