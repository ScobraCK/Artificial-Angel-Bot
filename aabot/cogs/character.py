from re import split

from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.views import show_view
from aabot.pagination import character as char_page
from aabot.pagination.skills import skill_view, skill_detail_view
from aabot.utils import api
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import apply_user_preferences, LanguageOptions
from aabot.utils.error import BotError
from common import schemas

class CharacterCommands(commands.Cog, name='Character Commands'):
    '''Commands related to characters'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
    language='Language to show character names. Defaults to English.'
    )
    @apply_user_preferences()
    async def idlist(
        self, 
        interaction: Interaction,
        language: LanguageOptions|None=None):
        '''
        Shows character ids
        '''
        name_data = await api.fetch_api(
            api.STRING_CHARACTER_PATH_ALL,
            query_params={'language': language},
            response_model=dict[int, schemas.Name]
        )
        view = char_page.id_list_view(interaction, name_data)
        await show_view(interaction, view)
    
    @app_commands.command()
    @app_commands.describe(
        add='Additional speed from speed runes',
        buffs='List of speed buff percentages',
    )
    @apply_user_preferences()
    async def speed(
        self, 
        interaction: Interaction, 
        add: int|None=0, 
        buffs: str|None=None,
        language: LanguageOptions|None=None):
        '''List character speeds in decreasing order'''
        name_data = await api.fetch_api(
            api.STRING_CHARACTER_PATH_ALL,
            response_model=dict[int, schemas.Name],
            query_params={'language': language}
        )
        
        speed_data = await api.fetch_api(
            api.CHARACTER_LIST_PATH,
            response_model=list[schemas.CharacterDBModel],
            query_params={'option': 'speed'}
        )
        
        if buffs is None:
            buff_list = None
        else:
            try:
                buff_list = [int(buff) for buff in split(r'[,\s]+', buffs) if buff]
            except ValueError:
                await interaction.response.send_message(
                    "Invalid input for buffs. Please enter a list of integers separated by commas or spaces. Example /speed `-15 15 30`", 
                    ephemeral=True
                    )
                return

        view = char_page.speed_view(interaction, speed_data, name_data, add, buff_list)
        await show_view(interaction, view)


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
        
        embed = char_page.char_info_embed(char_data, skill_data, self.bot.common_strings[language])

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

        view = skill_view(interaction, skill_data, char_data)
        await show_view(interaction, view)

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

        view = skill_detail_view(interaction, skill_data, char_data)
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
        
async def setup(bot: AABot):
	await bot.add_cog(CharacterCommands(bot))
