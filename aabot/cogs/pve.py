from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import pve as pve_ui
from aabot.pagination.view import BaseView
from aabot.utils.command_utils import apply_user_preferences
from aabot.utils.error import BotError
from aabot.utils.utils import to_quest_id
from common import enums
from common.database import SessionAA

class PvECommands(commands.Cog, name='PvE Commands'):
    '''Commands for pve information'''

    def __init__(self, bot: AABot):
        self.bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        stage='Quest stage id or string(ex.18-28)',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def quest(self, interaction: Interaction, stage: str, language: enums.LanguageOptions|None=None):
        '''
        Searches quest and enemy data for specified stage
        '''
        quest_id = to_quest_id(stage)
        if quest_id is None:
            raise BotError(f'Could not find stage `{stage}`')
        view = BaseView(await pve_ui.quest_ui(quest_id, language, self.bot.common_strings[language]), interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        floor='The floor of the tower',
        towertype='The tower type. Defaults to the Tower of Infinity',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def tower(
        self, interaction: Interaction, 
        floor: int, 
        towertype: enums.TowerType=enums.TowerType.Infinity,
        language: enums.LanguageOptions|None=None,
        ):
        '''
        Searches enemy data for specified tower floor

        Shows an overview as the main page and can select to see in detail
        '''
        view = BaseView(await pve_ui.tower_ui(floor, towertype, language, self.bot.common_strings[language]), interaction.user)
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(PvECommands(bot))