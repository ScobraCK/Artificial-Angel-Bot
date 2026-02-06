from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import mentemori as mentemori_ui
from aabot.pagination.view import BaseView
from aabot.utils.command_utils import apply_user_preferences
from common.enums import LanguageOptions, Server

class MentemoriCommands(commands.Cog, name='Mentemori Commands'):
    '''Commands that use data from mentemori.icu'''

    def __init__(self, bot: AABot):
        self.bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
        world='World'
    )
    @apply_user_preferences()
    async def temple(
        self,
        interaction: Interaction,
        server: Server|None = None,
        world: int|None = None
    ):
        '''View Temple'''
        await interaction.response.defer()
        view = BaseView(await mentemori_ui.temple_ui(server, world), interaction.user,)
        await view.update_view(interaction)

    @app_commands.command()
    async def groups(self, interaction: Interaction):
        """Show world groups"""
        await interaction.response.defer()
        view = BaseView(await mentemori_ui.group_ui(), interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        server='The region your world is in',
        world='Any world in the group you are searching for'
    )
    @apply_user_preferences()
    async def grouprankings(
        self,
        interaction: Interaction,
        server: Server|None = None,
        world: int|None = None
    ):             
        '''Guild rankings by group'''
        await interaction.response.defer()

        view = BaseView(await mentemori_ui.group_ranking_ui(server, world), interaction.user)
        await view.update_view(interaction)
            
    @app_commands.command(
        extras={'help': mentemori_ui.world_ids_help}
    )
    @app_commands.describe(
        server='Option to filter by server',
        world='Option to filter by world (only when server is specified)',
        world_ids='Standalone option to filter by multiple world ids'
    )
    async def guildrankings(
        self,
        interaction: Interaction,
        limit: app_commands.Range[int, 1, 1000]=500,
        server: Server|None = None,
        world: int|None = None,
        world_ids: str|None = None
    ):
        '''Guild rankings'''
        params, text = mentemori_ui.get_world_query(server, world, world_ids, limit)
        view = BaseView(await mentemori_ui.guild_ranking_ui(params, text), interaction.user)
        await view.update_view(interaction)

    @app_commands.command(
        extras={'help': mentemori_ui.world_ids_help}
    )
    @app_commands.describe(
        category='The ranking category (Default: BP)',
        limit='Number of results to show (Default: 1000, Max: 5000)',
        show_all='Show all categories (Default: False)',
        server='Option to filter by server',
        world='Option to filter by world (only when server is specified)',
        world_ids='Standalone option to filter by multiple world ids',
    )
    async def playerrankings(
        self,
        interaction: Interaction,
        category: mentemori_ui.PlayerCategory=mentemori_ui.PlayerCategory.BP,
        limit: app_commands.Range[int, 1, 5000]=1000,
        show_all: bool=False,
        server: Server|None = None,
        world: int|None = None,
        world_ids: str|None = None
    ):
        '''Player rankings for server'''
        params, text = mentemori_ui.get_world_query(server, world, world_ids, limit)
        params['order_by'] = category.value

        view = BaseView(await mentemori_ui.player_ranking_ui(params, text, category, show_all), interaction.user)
        await view.update_view(interaction)
        
    @app_commands.command(
        extras={'help': mentemori_ui.world_ids_help}
    )
    @app_commands.describe(
        category='The ranking category. Default BP',
        limit='Number of results to show (Default: 1000, Max: 5000)',
        server='Option to filter by server',
        world='Option to filter by world (only when server is specified)',
        world_ids='Standalone option to filter by multiple world ids',
    )
    async def towerrankings(
        self,
        interaction: Interaction,
        category: mentemori_ui.TowerCategory=mentemori_ui.TowerCategory.Infinity,
        limit: app_commands.Range[int, 1, 5000]=1000,
        server: Server|None = None,
        world: int|None = None,
        world_ids: str|None = None
    ):
        '''Tower rankings'''
        params, text = mentemori_ui.get_world_query(server, world, world_ids, limit)
        params['order_by'] = category.value

        view = BaseView(await mentemori_ui.tower_ranking_ui(params, text, category), interaction.user)
        await view.update_view(interaction)
        
    @app_commands.command()
    @app_commands.describe(
        server='Server to check IoC',
        gacha='Invocation of Chance (IoC) / Invocation of Stars Guidance (IoSG). Defaults to IoC.',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def gachalogs(
        self, 
        interaction: Interaction, 
        server: Server,
        gacha: mentemori_ui.GachaLog = mentemori_ui.GachaLog.IoC,
        language: LanguageOptions|None=None):
        '''Shows IoC and IoSG logs'''
        await interaction.response.defer()
        view = BaseView(
            await mentemori_ui.gacha_option_map(server),
            interaction.user,
            language=language,
            default_option=gacha.name
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        server='Option to filter by server',
    )
    async def raidrankings(self, interaction: Interaction, server: Server|None = None):
        """Show guild raid rankings"""
        view = BaseView(await mentemori_ui.raid_ranking_ui(server), interaction.user)
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(MentemoriCommands(bot))
