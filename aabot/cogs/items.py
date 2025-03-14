from typing import Optional

from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.api import api

from aabot.pagination.items import equipment_help_description
from aabot.pagination import items as item_response
from aabot.pagination.views import show_view
from aabot.utils.enums import Language
from aabot.utils.command_utils import apply_user_preferences

from aabot.utils.logger import get_logger
logger = get_logger(__name__)


class ItemCommands(commands.Cog, name='Item Commands'):
    '''Commands related to items'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
        item_id='Item id',
        item_type="Item type",
        language="Text language. Defaults to English."
    )
    @apply_user_preferences()
    async def finditem(
        self, interaction: Interaction, 
        item_id: int, 
        item_type: int,
        language: Optional[Language]=None):
        '''
        Command for quick searching from ItemId and ItemType
        '''
        
        item_data = await api.fetch_item(item_id, item_type, language)  # directly use fetch item
        embed = item_response.item_embed(item_data)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(
        extras={'help': equipment_help_description}
    )
    @app_commands.describe(
        string="Search string. Use /help equipment for instructions.",
        language="Text language. Defaults to English."
    )
    @apply_user_preferences()
    async def equipment(
        self, interaction: Interaction, 
        string: str,
        language: Optional[Language]=None
    ):
        view = await item_response.equipment_view(interaction, string, language)
        await show_view(interaction, view)

async def setup(bot):
	await bot.add_cog(ItemCommands(bot))