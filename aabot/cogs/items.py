from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.equipment import equipment_help_description, equipment_option_map
from aabot.pagination import items as item_ui
from aabot.pagination.view import BaseView
from aabot.utils.command_utils import apply_user_preferences, itemtype_autocomplete
from common import enums


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
    @app_commands.autocomplete(item_type=itemtype_autocomplete)
    @apply_user_preferences()
    async def finditem(
        self, interaction: Interaction, 
        item_id: int, 
        item_type: int,
        language: enums.LanguageOptions|None=None):
        '''
        Command for quick searching from ItemId and ItemType
        '''
        view = BaseView(
            await item_ui.item_ui(item_id, item_type, language, self.bot.common_strings[language]),
            interaction.user
        )
        await view.update_view(interaction)
        
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
        language: enums.LanguageOptions|None=None):
        '''Shows equipment information'''
        await interaction.response.defer()
        view = BaseView(
            await equipment_option_map(string, language, self.bot.common_strings[language]),
            interaction.user
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        rune='Rune',
        language="Text language. Defaults to English."
    )
    @apply_user_preferences()
    async def rune(
        self, interaction: Interaction,
        rune: enums.RuneType,
        language: enums.LanguageOptions|None=None):
        '''Shows rune information'''
        view = BaseView(
            await item_ui.rune_ui(rune, language, self.bot.common_strings[language]),
            interaction.user
        )
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(ItemCommands(bot))