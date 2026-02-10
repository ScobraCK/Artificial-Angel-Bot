from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.view import BaseView
from aabot.pagination import character as char_ui
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import apply_user_preferences
from common.enums import LanguageOptions

class CharacterCommands(commands.Cog, name='Character Commands'):
    '''Commands for charactere information. All other commands can be selected as an option menu once a response is sent.'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
    character='The name or id of the character',
    language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def character(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):  
        '''Shows a character's basic info'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.INFO.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
    character='The name or id of the character',
    language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def profile(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):  
        '''Shows a character's profile info'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.PROFILE.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def skill(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows character skills including unique weapon upgrade effects'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.SKILL.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def uniqueweapon(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows unique weapon data'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.UW.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def arcana(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None
    ):  
        '''Shows character arcana data'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.ARCANA.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def voicelines(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows character voicelines'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.VOICELINES.value
        )
        await view.update_view(interaction)
        
    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def memories(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows character memories'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.MEMORIES.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def lament(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows character lament'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.LAMENT.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def basestats(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows initial character stats as shown in index'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.STATS.value
        )
        await view.update_view(interaction)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def gachahistory(
        self, 
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: LanguageOptions|None=None):
        '''Shows gacha history of a character'''
        content = await char_ui.character_option_map(character)
        view = BaseView(
            content,
            interaction.user,
            language,
            self.bot.common_strings[language],
            default_option=char_ui.CharacterOptions.GACHA.value
        )
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(CharacterCommands(bot))
