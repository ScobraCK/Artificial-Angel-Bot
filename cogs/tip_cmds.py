import discord
from discord import app_commands
from discord.ext import commands

import common
import timezones
from typing import Optional
from io import StringIO
from my_view import My_View

def get_dailyinfo(server: timezones.ServerUTC):
    text = StringIO()
    info = timezones.DailyEvents()
    local = timezones.unix_to_local
    text.write(f'<t:{local(info.reset, server)}:t> Daily Server Reset\n')
    text.write(f'<t:{local(info.shop1, server)}:t> Free Shop Reset A\n')
    text.write(f'<t:{local(info.shop2, server)}:t> Free Shop Reset B\n')
    text.write(f'<t:{local(info.shop3, server)}:t> Free Shop Reset C\n')
    text.write(f'<t:{local(info.shop4, server)}:t> Free Shop Reset D\n\n')
    text.write(f'<t:{local(info.temple_open1, server)}:t>~<t:{local(info.temple_close1, server)}:t> Temple of Illusion A\n')
    text.write(f'<t:{local(info.temple_open2, server)}:t>~<t:{local(info.temple_close2, server)}:t> Temple of Illusion B\n\n')
    text.write(f'<t:{local(info.guild_strategy_start, server)}:t>~<t:{local(info.guild_strategy_end, server)}:t> Guild Battle: Strategy Phase\n')
    text.write(f'<t:{local(info.guild_war_start, server)}:t>~<t:{local(info.guild_war_end, server)}:t> Guild Battle: War Phase\n\n')
    text.write(f'<t:{local(info.grand_strategy_start, server)}:t>~<t:{local(info.grand_strategy_end, server)}:t> Grand Battle: Strategy Phase\n')
    text.write(f'<t:{local(info.grand_war_start, server)}:t>~<t:{local(info.grand_war_end, server)}:t> Grand Battle: War Phase\n\n')
    text.write(f'<t:{local(info.grand_first_strategy, server)}:t>~<t:{local(info.grand_strategy_end, server)}:t> Grand Battle: Strategy Phase **[Start of Season]**\n\n')

    return text.getvalue()

def daily_embed(server: timezones.ServerUTC):
    server_name = server.name.replace('_', '/')

    embed=discord.Embed(
        title = f'Daily Information [{server_name}]',
        description=get_dailyinfo(server),
        color=discord.Colour.blue()
        )
    return embed

class DailyView(My_View):
    def __init__(self, user: discord.User):
        super().__init__(user)

    async def update_button(self, button: discord.ui.Button):
        for btn in self.children:
            if btn is button:
                btn.disabled=True
            else:
                btn.disabled=False

    @discord.ui.button(label="NA")
    async def na_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=daily_embed(timezones.ServerUTC.NA), view=self)
        
    @discord.ui.button(label="EU/GL")
    async def eu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=daily_embed(timezones.ServerUTC.EU_GL), view=self)

    @discord.ui.button(label="JP/KR")
    async def jp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=daily_embed(timezones.ServerUTC.JP_KR), view=self)

    @discord.ui.button(label="ASIA")
    async def asia_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=daily_embed(timezones.ServerUTC.ASIA), view=self)


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

    @app_commands.command()
    async def dailyinfo(self, interaction: discord.Interaction, 
                        server: Optional[timezones.ServerUTC] = timezones.ServerUTC.NA):
        '''List of notable daily events shown in local time'''
        
        embed = daily_embed(server)

        user = interaction.user
        view = DailyView(user)

        if server == timezones.ServerUTC.NA:
            first_btn = view.na_btn
        elif server == timezones.ServerUTC.JP_KR:
            first_btn = view.jp_btn
        elif server == timezones.ServerUTC.EU_GL:
            first_btn = view.eu_btn
        else:
            first_btn = view.asia_btn

        await view.update_button(first_btn)
        await interaction.response.send_message(embed=embed, view=view)

        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Tips(bot))