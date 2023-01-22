import discord
from discord import app_commands
from discord.ext import commands
from typing import Iterable, Tuple, List

import character
import common
from my_view import My_View

def speed_text(masterdata, max: int=20) -> Tuple[str, List]:
    '''
    get first 20(max) characters and also returns the speed iter
    '''
    speed_it = character.speed_iter(masterdata)
    text = ''
    try:
        for i in range(1, max+1):
            speed = next(speed_it)
            text += f"**{i}.** {common.id_list[speed[0]]} {speed[1]}\n"
    except StopIteration:
        pass

    return text, speed_it

class Speed_View(My_View):
    def __init__(self, user: discord.User, embed: discord.Embed, speed_it: Iterable):
        super().__init__(user)
        self.it = speed_it
        self.embed = embed
        
    @discord.ui.button(label="Show All")
    async def btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled=True
        text = ''
        for i, speed in enumerate(self.it, 21):  # 20 is already shown
            text += f"**{i}.** {common.id_list[speed[0]]} {speed[1]}\n"
        self.embed.description += text
        await interaction.response.edit_message(embed=self.embed, view=self)

class Character_Search(commands.Cog, name='Search Commands'):
    '''These are helpful tip commands'''

    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command()
    async def speed(self, interaction: discord.Interaction):
        '''List character speeds in decreasing order'''
        text, speed_it = speed_text(self.bot.masterdata)
        embed = discord.Embed(
            title='Character Speeds',
            description=text)
        user = interaction.user
        view = Speed_View(user, embed, speed_it)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Character_Search(bot))