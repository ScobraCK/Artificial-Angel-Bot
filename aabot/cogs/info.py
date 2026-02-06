from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import info as info_ui
from aabot.pagination.view import BaseView
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import apply_user_preferences, arcana_autocomplete, ArcanaOption, ArcanaOptions
from common.enums import LanguageOptions

class InfoCommands(commands.Cog, name='Info Commands'):
    '''Commands for uncategorized information about characters and game data'''
    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
        language='Text language. Defaults to English.',
        page_limit='Number of entries per page. Range:10-50. Defaults to 20.'
    )
    @apply_user_preferences()
    async def idlist(
        self, 
        interaction: Interaction,
        page_limit: app_commands.Range[int, 10, 50]=20,
        language: LanguageOptions|None=None):
        '''
        Shows character ids
        '''
        view = BaseView(await info_ui.id_list_ui(language, page_limit), interaction.user)
        await view.update_view(interaction)
    
    @app_commands.command()
    @app_commands.describe(
        flat='Flat speed as such from speed runes',
        mult='Speed buff multiplier percentage',
        page_limit='Number of entries per page. Range:10-50. Defaults to 20.'
    )
    @apply_user_preferences()
    async def speed(
        self, 
        interaction: Interaction, 
        flat: int|None=0,
        mult: int|None=0,
        page_limit: app_commands.Range[int, 10, 50]=20,
        language: LanguageOptions|None=None):
        '''List character speeds in decreasing order'''
        view = BaseView(await info_ui.speed_ui(language, flat=flat, mult=mult, page_limit=page_limit), interaction.user, language=language)
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def skilldetails(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows character skills and details'''

        view = BaseView(await info_ui.skill_detail_ui(character, language), interaction.user, language=language)
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='Character filter option',
        filter_option='Filter options for arcana bonus',
        language='Text language. Defaults to English.'
    )
    @app_commands.autocomplete(filter_option=arcana_autocomplete)
    @apply_user_preferences()
    async def searcharcana(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer]|None=None,
        filter_option: str|None=None,
        language: LanguageOptions|None=None
    ):  
        '''Shows arcana data'''
        if filter_option is not None:
            if filter_option not in ArcanaOptions:
                await interaction.response.send_message(
                    f"Invalid filter option: {filter_option}. Please choose from a given option.",
                    ephemeral=True
                )
                return

            option = ArcanaOptions[filter_option]
        else:
            option = ArcanaOption()

        await interaction.response.defer()

        view = BaseView(
            await info_ui.arcana_search_ui(character, option, self.bot.common_strings[language], language),
            interaction.user,
            language=language,
            cs=self.bot.common_strings[language]
        )  
        
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(InfoCommands(bot))
