import discord
from discord import app_commands
from discord.ext import commands

import common
import timezones
from typing import Optional, Tuple
from io import StringIO
from pagination import MyView
from itertools import dropwhile

def get_dailyinfo(server: timezones.ServerUTC):
    text = StringIO()
    info = timezones.DailyEvents()
    local = timezones.unix_to_local
    text.write(f'<t:{local(info.reset, server)}:t> Daily Server Reset\n')
    text.write(f'<t:{local(info.shop1, server)}:t> Free Shop Reset A\n')
    text.write(f'<t:{local(info.shop2, server)}:t> Free Shop Reset B\n')
    text.write(f'<t:{local(info.shop3, server)}:t> Free Shop Reset C\n')
    text.write(f'<t:{local(info.shop4, server)}:t> Free Shop Reset D\n\n')
    text.write(f'<t:{local(info.temple_open1, server)}:t>~<t:{local(info.temple_close1, server)}:t> Temple of Illusion Boost\n')
    text.write(f'<t:{local(info.temple_open2, server)}:t>~<t:{local(info.temple_close2, server)}:t> Temple of Illusion Boost\n\n')
    text.write(f'<t:{local(info.guild_strategy_start, server)}:t>~<t:{local(info.guild_strategy_end, server)}:t> Guild/Grand Battle: Strategy Phase\n')
    text.write(f'<t:{local(info.guild_war_start, server)}:t>~<t:{local(info.guild_war_end, server)}:t> Guild/Grand Battle: War Phase\n\n')
    # text.write(f'<t:{local(info.grand_strategy_start, server)}:t>~<t:{local(info.grand_strategy_end, server)}:t> Grand Battle: Strategy Phase\n')
    # text.write(f'<t:{local(info.grand_war_start, server)}:t>~<t:{local(info.grand_war_end, server)}:t> Grand Battle: War Phase\n\n')
    # text.write(f'<t:{local(info.grand_first_strategy, server)}:t>~<t:{local(info.grand_strategy_end, server)}:t> Grand Battle: Strategy Phase **[Start of Season]**\n\n')

    return text.getvalue()

def daily_embed(server: timezones.ServerUTC):
    server_name = server.name.replace('_', '/')

    embed=discord.Embed(
        title = f'Daily Information [{server_name}]',
        description=get_dailyinfo(server),
        color=discord.Colour.blue()
        )
    return embed

########## levellink #################
def get_sublevel(level: float)->Tuple[int, int]:
    level = str(level)
    try:
        base, sub = level.split('.')
        base = int(base)
        sub = int(sub[0])
    except ValueError:
        base = int(level)
        sub = 0

    return base, sub

def level_predicate(leveldata, base, sub):
    if leveldata['PartyLevel'] < base:
        return True
    if leveldata['PartySubLevel'] < sub:
        return True
    return False

#######################################

class DailyView(MyView):
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

    @app_commands.command()
    @app_commands.describe(
        startlevel='specify sublevel if required. 240(=240.0), 240.1, 240.9',
        endlevel='rounds to the next power of 10 if empty (sublevel is 0)'
    )
    async def levellink(
        self,
        interaction: discord.Interaction,
        startlevel: float,
        endlevel: Optional[float]):
        '''
        Calculate level link costs.
        '''

        startbase, startsub = get_sublevel(startlevel)
        if endlevel:
            endbase, endsub = get_sublevel(endlevel)
        else:
            endlevel = endbase = int((startbase+10) / 10) * 10
            endsub = 0

        if startlevel < 240:
            await interaction.response.send_message(
                "Currently only levellink(240+) is supported.",
                ephemeral=True
            )

        elif startlevel > endlevel:
            await interaction.response.send_message(
                f"startlevel should be lower than baselevel. Got `{startlevel}` and `{endlevel}`.",
                ephemeral=True
            )       

        else:
            link_data_MB = self.bot.masterdata.get_MB_iter("LevelLinkMB")                
            link_data_list = list(link_data_MB)
            
            max_level = link_data_list[-1]['PartyLevel']
            if endbase == max_level + 1:
                endsub = 0
            if startlevel > max_level or endbase > max_level+1:
                await interaction.response.send_message(
                    f"Max level is {max_level}.9",
                    ephemeral=True
                )
            else:
                level_data = dropwhile(lambda x: level_predicate(x, startbase, startsub), link_data_list)
                total_gold = 0
                total_gorb = 0
                total_rorb = 0
                for level in level_data:
                    if level['PartyLevel'] == endbase and level['PartySubLevel'] == endsub:  # end
                        break
                    costs = level['RequiredLevelUpItems']
                    total_gold += costs[0]["ItemCount"]  # gold
                    total_gorb += costs[1]["ItemCount"]  # green orbs
                    if len(costs) == 3:
                        total_rorb += costs[2]["ItemCount"]  # red orbs      
                
                embed = discord.Embed(
                    title='Level Link Costs',
                    description=(
                        f"**__{startbase}.{startsub} -> {endbase}.{endsub}__**\n"
                        f"Gold: {total_gold:,d}\n"
                        f"Green Orbs: {total_gorb:,d}\n"
                        f"Red Orbs: {total_rorb:,d}\n"
                    ),
                    color=discord.Color.dark_gold()
                )

                await interaction.response.send_message(embed=embed)


async def setup(bot):
	await bot.add_cog(Tips(bot))