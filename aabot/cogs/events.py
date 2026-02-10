from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import events as event_page
from aabot.pagination.view import BaseView
from aabot.utils.command_utils import apply_user_preferences
from common.enums import LanguageOptions


class EventCommands(commands.Cog, name='Event Commands'):
    '''Commands for ingame events and gacha'''

    def __init__(self, bot):
        self.bot: AABot = bot
    
    @app_commands.command()
    @app_commands.describe(
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def gachabanner(
        self,
        interaction: Interaction,
        language: LanguageOptions|None=None):
        '''Shows gacha banners'''
        view = BaseView(await event_page.gacha_banner_ui(language), interaction.user)
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(EventCommands(bot))