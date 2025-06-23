from re import split

from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import mentemori as mentemori_page
from aabot.pagination.views import show_view
from aabot.utils import api
from aabot.utils.command_utils import apply_user_preferences, LanguageOptions
from aabot.utils.utils import to_world_id
from common import schemas
from common.enums import Server


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
        world_id = to_world_id(server, world)
        resp = await api.fetch(
            url=api.MENTEMORI_TEMPLE_PATH.format(world_id=world_id),
            base_url=api.MENTEMORI_BASE_PATH
        )
        data = resp.json()

        embed = mentemori_page.temple_embed(data, server, world)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command()
    async def groups(self, interaction: Interaction):
        """Show world groups"""

        resp = await api.fetch(
            api.MENTEMORI_GROUP_PATH,
            base_url=api.MENTEMORI_BASE_PATH
        )
        group_data = resp.json()
        embed = mentemori_page.group_embed(group_data)
        
        await interaction.response.send_message(embed=embed)

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
        world_id = to_world_id(server, world)
        worlds = None
        group_id = None

        resp = await api.fetch(
            api.MENTEMORI_GROUP_PATH,
            base_url=api.MENTEMORI_BASE_PATH
        )
        group_data = resp.json()
        for group in group_data['data']:
            if world_id in group['worlds']:
                worlds = group['worlds']
                group_id = group['group_id']
                break
        
        if not worlds:
            await interaction.response.send_message(
                f"Group for `{server.name} W{world}` was not found",
                ephemeral=True
            )
            return

        ranking_data = await api.fetch_api(
            api.GUILD_RANKING_PATH,
            response_model=list[schemas.GuildRankInfo],
            query_params={'count': 200, 'world_id': worlds}
        )

        view = mentemori_page.group_ranking_view(interaction, ranking_data, server, group_id)
        await show_view(interaction, view)
            
    @app_commands.command(
        extras={'help': mentemori_page.world_ids_help}
    )
    @app_commands.describe(
        server='Option to filter by server',
        world='Option to filter by world (only when server is specified)',
        world_ids='Standalone option to filter by multiple world ids'
    )
    async def guildrankings(
        self,
        interaction: Interaction,
        server: Server|None = None,
        world: int|None = None,
        world_ids: str|None = None
    ):
        '''Guild rankings'''
        if world and not server:
            await interaction.response.send_message(
                "Cannot use `world` without `server`",
                ephemeral=True
            )
            return
        
        filter_text = 'All'
        query_params = {'count': 500}

        if world_ids:
            try:
                world_ids = list(map(int, split(r'[,\s]+', world_ids.strip())))
                for world_id in world_ids:
                    if not (1000 <= world_id <= 7000):  # Simple check for invalid world ids
                        raise ValueError()
            except ValueError:
                await interaction.response.send_message(
                    mentemori_page.world_ids_help(),
                    ephemeral=True
                )
                return
            filter_text = ', '.join(map(str, world_ids))
            query_params['world_id'] = world_ids
        elif world:
            filter_text = f'{server.name} {world}'
            query_params['world_id'] = to_world_id(server, world)
        elif server:
            filter_text = server.name
            query_params['server'] = server

        ranking_data = await api.fetch_api(
            api.GUILD_RANKING_PATH,
            response_model=list[schemas.GuildRankInfo],
            query_params=query_params
        )
                
        view = mentemori_page.guild_ranking_view(interaction, ranking_data, filter_text)
        await show_view(interaction, view)

    @app_commands.command(
        extras={'help': mentemori_page.world_ids_help}
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
        category: mentemori_page.PlayerCategory=mentemori_page.PlayerCategory.BP,
        limit: app_commands.Range[int, 1, 5000]=1000,
        show_all: bool=False,
        server: Server|None = None,
        world: int|None = None,
        world_ids: str|None = None
    ):
        '''Player rankings for server'''
        if world and not server:
            await interaction.response.send_message(
                "Cannot use `world` without `server`",
                ephemeral=True
            )
            return
        
        filter_text = 'All'
        query_params = {'count': limit, 'order_by': category.value}

        if world_ids:
            try:
                world_ids = list(map(int, split(r'[,\s]+', world_ids.strip())))
                for world_id in world_ids:
                    if not (1000 <= world_id <= 7000):  # Simple check for invalid world ids
                        raise ValueError()
            except ValueError:
                await interaction.response.send_message(
                    mentemori_page.world_ids_help(),
                    ephemeral=True
                )
                return
            filter_text = ', '.join(map(str, world_ids))
            query_params['world_id'] = world_ids
        elif world:
            filter_text = f'{server.name} {world}'
            query_params['world_id'] = to_world_id(server, world)
        elif server:
            filter_text = server.name
            query_params['server'] = server

        ranking_data = await api.fetch_api(
            api.PLAYER_RANKING_PATH,
            response_model=list[schemas.PlayerRankInfo],
            query_params=query_params
        )
                
        view = mentemori_page.player_ranking_view(interaction, ranking_data, category, filter_text, show_all)
        await show_view(interaction, view)
        
    @app_commands.command(
        extras={'help': mentemori_page.world_ids_help}
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
        category: mentemori_page.TowerCategory=mentemori_page.TowerCategory.Infinity,
        limit: app_commands.Range[int, 1, 5000]=1000,
        server: Server|None = None,
        world: int|None = None,
        world_ids: str|None = None
    ):
        '''Tower rankings'''
        if world and not server:
            await interaction.response.send_message(
                "Cannot use `world` without `server`",
                ephemeral=True
            )
            return
        
        filter_text = 'All'
        query_params = {'count': limit, 'order_by': category.value}

        if world_ids:
            try:
                world_ids = list(map(int, split(r'[,\s]+', world_ids.strip())))
                for world_id in world_ids:
                    if not (1000 <= world_id <= 7000):  # Simple check for invalid world ids
                        raise ValueError()
            except ValueError:
                await interaction.response.send_message(
                    mentemori_page.world_ids_help(),
                    ephemeral=True
                )
                return
            filter_text = ', '.join(map(str, world_ids))
            query_params['world_id'] = world_ids
        elif world:
            filter_text = f'{server.name} {world}'
            query_params['world_id'] = to_world_id(server, world)
        elif server:
            filter_text = server.name
            query_params['server'] = server

        ranking_data = await api.fetch_api(
            api.PLAYER_RANKING_PATH,
            response_model=list[schemas.PlayerRankInfo],
            query_params=query_params
        )
                
        view = mentemori_page.tower_ranking_view(interaction, ranking_data, category,filter_text)

        await show_view(interaction, view)
        
    @app_commands.command()
    @app_commands.describe(
        gacha='Invocation of Chance (IoC) / Invocation of Stars Guidance (IoSG)',
        server='Server to check IoC',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def gachalogs(
        self, 
        interaction: Interaction, 
        gacha: mentemori_page.GachaLog,
        server: Server,
        language: LanguageOptions|None=None):
        '''Shows IoC or IoSG logs'''
        await interaction.response.defer()
        view = await mentemori_page.gacha_view(interaction, gacha, server, language)
        await show_view(interaction, view, defered=True)


async def setup(bot: AABot):
	await bot.add_cog(MentemoriCommands(bot))
