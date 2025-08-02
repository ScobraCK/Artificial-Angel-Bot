from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import pve as pve_page
from aabot.pagination.views import show_view
from aabot.utils import api
from aabot.utils.error import BotError
from aabot.utils.utils import to_quest_id
from common import schemas
from common.enums import TowerType
from common.database import SessionAA

class PvECommands(commands.Cog, name='PvE Commands'):
    '''Commands for pve information'''

    def __init__(self, bot: AABot):
        self.bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        stage='Quest stage id or string(ex.18-28)'
    )
    async def quest(self, interaction: Interaction, stage: str):
        '''
        Searches quest and enemy data for specified stage

        Shows an overview as the main page and can select to see in detail
        '''
        quest_id = to_quest_id(stage)
        if quest_id is None:
            raise BotError(f'Could not find stage `{stage}`')
        
        quest_data = await api.fetch_api(
            api.QUEST_PATH.format(quest_id=quest_id), 
            response_model=schemas.Quest,
            query_params={'language': 'enus'}  # TODO add later
        )
        async with SessionAA() as session:
            view = await pve_page.quest_view(interaction, quest_data, session, self.bot.common_strings['enus'])  # spacing issue for other languages
        await show_view(interaction, view)

    @app_commands.command()
    @app_commands.describe(
        floor='The floor of the tower',
        towertype="The tower type. Defaults to the Tower of Infinity"
    )
    async def tower(
        self, interaction: Interaction, 
        floor: int, 
        towertype: TowerType=TowerType.Infinity):
        '''
        Searches enemy data for specified tower floor

        Shows an overview as the main page and can select to see in detail
        '''
        
        tower_data = await api.fetch_api(
            api.TOWER_PATH,
            response_model=schemas.Tower,
            query_params={
                'floor': floor,
                'tower_type': towertype,
                'language': 'enus'  # TODO add later
            }
        )
        async with SessionAA() as session:
            view = await pve_page.tower_view(interaction, tower_data, session, self.bot.common_strings['enus'])  # spacing issue for other languages
        await show_view(interaction, view)


async def setup(bot: AABot):
	await bot.add_cog(PvECommands(bot))