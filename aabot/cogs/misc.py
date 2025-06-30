from itertools import dropwhile

from discord import app_commands, Color, Embed, Interaction
from discord.ext import commands

from aabot.db.alias import get_alias
from aabot.main import AABot
from aabot.pagination import misc as misc_page
from aabot.pagination.views import show_view
from aabot.utils import api
from aabot.utils.alias import IdTransformer
from aabot.utils.assets import RAW_ASSET_BASE
from aabot.utils.command_utils import apply_user_preferences
from aabot.utils.error import BotError
from aabot.utils.utils import character_title
from common.database import AsyncSession as SessionAABot
from common.enums import Server

class MiscCommands(commands.Cog, name='Misc Commands'):
    '''These are helpful miscellaneous commands'''

    def __init__(self, bot: AABot):
        self.bot = bot
    
    @app_commands.command()
    async def awakening(self, interaction: Interaction):
        '''Awakening cost chart'''
        embed=Embed()
        img = RAW_ASSET_BASE + 'Bot/awakening_costs.png'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def soulaffinity(self, interaction: Interaction):
        '''Soul affinity chart'''
        embed=Embed()
        img = RAW_ASSET_BASE + 'Bot/soul_affinity.jpg'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def enhancecost(self, interaction: Interaction):
        '''Equipment enhancement cost chart'''
        embed=Embed()
        img = RAW_ASSET_BASE + 'Bot/enhance.png'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def seteffect(self, interaction: Interaction):
        '''Equipment set effect chart'''
        embed=Embed()
        img = RAW_ASSET_BASE + 'Bot/seteffects.png'
        embed.set_image(url=img)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    @apply_user_preferences()
    async def dailyinfo(self,
                        interaction: Interaction, 
                        server: Server|None = None):
        '''list of notable daily events shown in local time'''
        
        view = misc_page.daily_view(interaction, server)
        await show_view(interaction, view)


    # TODO redo levellink
    @app_commands.command()
    @app_commands.describe(
        startlevel='specify sublevel if required. 240(=240.0), 240.1, 240.9',
        endlevel='rounds to the next power of 10 if empty (sublevel is 0)'
    )
    async def levellink(
        self,
        interaction: Interaction,
        startlevel: float,
        endlevel: float|None):
        '''
        Calculate level link costs.
        '''

        startbase, startsub = misc_page.get_sublevel(startlevel)
        if endlevel:
            endbase, endsub = misc_page.get_sublevel(endlevel)
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
            link_data = await api.fetch_api(
                api.MASTER_PATH.format(mb='LevelLinkMB'),
                response_model=list[dict]
            )               
            link_data_list = link_data.data
            
            max_level = link_data_list[-1]['PartyLevel']
            if endbase == max_level + 1:
                endsub = 0
            if startlevel > max_level or endbase > max_level+1:
                await interaction.response.send_message(
                    f"Max level is {max_level}.9",
                    ephemeral=True
                )
            else:
                level_data = dropwhile(lambda x: misc_page.level_predicate(x, startbase, startsub), link_data_list)
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
                
                embed = Embed(
                    title='Level Link Costs',
                    description=(
                        f"**__{startbase}.{startsub} -> {endbase}.{endsub}__**\n"
                        f"Gold: {total_gold:,d}\n"
                        f"Green Orbs: {total_gorb:,d}\n"
                        f"Red Orbs: {total_rorb:,d}\n"
                    ),
                    color=Color.dark_gold()
                )

                await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(
        character = 'The name or id of the character'
    )
    async def alias(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer]
    ):
        async with SessionAABot() as session:
            aliases = await get_alias(session, character)
            if not aliases:
                await interaction.response.send_message(f'No alias found for character `{character}`.')
                return
            
            name = await api.fetch_name(character)

            embed = misc_page.alias_embed(character_title(name.data.title, name.data.name), aliases)
            await interaction.response.send_message(embed=embed)


async def setup(bot: AABot):
	await bot.add_cog(MiscCommands(bot))