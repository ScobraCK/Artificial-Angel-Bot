from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import events as event_page
from aabot.pagination.view import BaseView, to_content
from aabot.utils.alias import IdTransformer
from common.enums import LanguageOptions


class EventCommands(commands.Cog, name='Event Commands'):
    '''Commands for ingame events and gacha'''

    def __init__(self, bot):
        self.bot: AABot = bot
    
    @app_commands.command()
    @app_commands.describe(
        language='Text language. Defaults to English.'
    )
    async def gachabanner(
        self,
        interaction: Interaction,
        language: LanguageOptions|None=None):
        '''Shows gacha banners'''
        view = BaseView(to_content(await event_page.gacha_banner_ui(language)), interaction.user)
        await view.update_view(interaction)
    
    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    async def gachahistory(
        self, 
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows gacha history of a character'''
        view = BaseView(to_content(await event_page.gacha_banner_ui(language, character)), interaction.user)
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(EventCommands(bot))