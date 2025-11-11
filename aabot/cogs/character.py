from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.views import show_view
from aabot.pagination import character as char_page
from aabot.pagination.skills import skill_view
from aabot.utils import api
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import apply_user_preferences
from aabot.utils.error import BotError
from common import schemas
from common.database import SessionAA
from common.enums import LanguageOptions

class CharacterCommands(commands.Cog, name='Character Commands'):
    '''Commands for charactere information.'''

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

        char_data = await api.fetch_api(
            api.CHARACTER_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.Character
        )
        try:
            skill_data = await api.fetch_api(
                api.CHARACTER_SKILL_PATH,
                path_params={'char_id': character},
                query_params={'language': language},
                response_model=schemas.Skills
            )
        except BotError as e:
            skill_data = None  # Case where skill data is not avaliable when basic info is
        
        embed = await char_page.char_info_embed(char_data, skill_data, self.bot.common_strings[language])

        await interaction.response.send_message(embed=embed)

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

        profile_data = await api.fetch_api(
            api.CHARACTER_PROFILE_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.Profile
        )
        name = await api.fetch_name(character, language)
        
        embed = char_page.profile_embed(profile_data, name)

        await interaction.response.send_message(embed=embed)

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

        skill_data = await api.fetch_api(
            api.CHARACTER_SKILL_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.Skills
        )

        char_data = await api.fetch_api(
            api.CHARACTER_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.Character
        )
        async with SessionAA() as session:
            view = await skill_view(interaction, skill_data, char_data, session)
        await show_view(interaction, view)


            
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

        # f'{moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{}'

        voice_data = await api.fetch_api(
            api.CHARACTER_VOICE_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.CharacterVoicelines
        )

        profile_data = await api.fetch_api(
            api.CHARACTER_PROFILE_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.Profile
        )

        view = await char_page.voiceline_view(interaction, voice_data, profile_data, language)
        await show_view(interaction, view)
        
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
        memory_data = await api.fetch_api(
            api.CHARACTER_MEMORY_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=schemas.CharacterMemories
        )

        view = await char_page.memory_view(interaction, memory_data, language)
        await show_view(interaction, view)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @apply_user_preferences()
    async def arcana(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer]|None=None,
        language: LanguageOptions|None=None
    ):  
        '''Shows arcana data'''
        pass
        # arcana_data = await api.fetch_api(
        #     api.ARCANA_PATH,
        #     response_model=list[schemas.Arcana],
        #     query_params={
        #         'character': character,
        #         'param_category': options.category,
        #         'param_type': options.type,
        #         'param_change_type': options.change_type,
        #         'level_bonus': options.level_bonus,
        #         'language': language
        #     }
        # )

        # view = await char_page.arcana_view(interaction, arcana_data, self.bot.common_strings[language], language)
        # await show_view(interaction, view)

    @app_commands.command()
    async def test(self, interaction: Interaction):
        from aabot.pagination.view import BaseView, to_content
        try:
            container = await char_page.character_info_ui(117, LanguageOptions.enus, self.bot.common_strings[LanguageOptions.enus])
            view = BaseView(
                to_content(container),
                user=interaction.user,
                language=LanguageOptions.enus,
                cs=self.bot.common_strings[LanguageOptions.enus]
            )
            await view.update_view(interaction)
        except Exception as e:
            # raise BotError(str(e))
            raise e


async def setup(bot: AABot):
	await bot.add_cog(CharacterCommands(bot))
