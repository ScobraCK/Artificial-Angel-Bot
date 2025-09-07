from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.items import equipment_help_description
from aabot.pagination import items as item_response
from aabot.pagination.views import show_view
from aabot.utils import api
from aabot.utils.command_utils import apply_user_preferences, LanguageOptions
from common import enums
from common.database import SessionAA

async def itemtype_autocomplete(interaction: Interaction, current: int):
    choices = [
        app_commands.Choice(name=opt.name, value=opt.value) for opt in enums.ItemType
    ]
    return choices[:25]

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
        language: LanguageOptions|None=None):
        '''
        Command for quick searching from ItemId and ItemType
        '''
        if item_type not in enums.ItemType:
            await interaction.response.send_message(f"Invalid item type. See below:\n{'\n'.join([f'{item.value} - {item.name}' for item in enums.ItemType])}", ephemeral=True)
            return

        item_data = await api.fetch_item(item_id, item_type, language)  # directly use fetch item
        embed = item_response.item_embed(item_data, self.bot.common_strings[language])
        
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
        language: LanguageOptions|None=None):
        '''Shows equipment information'''
        await interaction.response.defer()
        async with SessionAA() as session:
            view = await item_response.equipment_view(interaction, string, session, self.bot.common_strings[language], language)
        await show_view(interaction, view)

    @app_commands.command()
    @app_commands.describe(
        rune='Rune',
        language="Text language. Defaults to English."
    )
    @apply_user_preferences()
    async def rune(
        self, interaction: Interaction,
        rune: enums.RuneType,
        language: LanguageOptions|None=None):
        '''Shows rune information'''
        view = await item_response.rune_view(interaction, rune, self.bot.common_strings[language], language)
        await show_view(interaction, view)


async def setup(bot: AABot):
	await bot.add_cog(ItemCommands(bot))