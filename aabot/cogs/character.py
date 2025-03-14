import re
from typing import Optional, Dict, List

from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.api import api, response
from aabot.pagination.views import show_view
from aabot.pagination import character as char_page
from aabot.pagination.skills import skill_view, skill_detail_view

from aabot.utils.error import BotError
from aabot.utils.enums import Language
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import apply_user_preferences



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
        language: Optional[Language]=None):
        '''
        Shows character ids
        '''
        name_data = await api.fetch_api(
            api.STRING_CHARACTER_PATH_ALL,
            query_params={'language': language},
            response_model=Dict[int, response.Name]
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
        add: Optional[int]=0, 
        buffs: Optional[str]=None,
        language: Optional[Language]=None):
        '''List character speeds in decreasing order'''
        name_resp = await api.fetch_api(
            api.STRING_CHARACTER_PATH_ALL,
            query_params={'language': language}
        )
        name_data = api.parse_response(name_resp, Dict[int, response.Name])
        
        speed_resp = await api.fetch_api(
            api.CHARACTER_LIST_PATH,
            query_params={'option': 'speed'}
        )
        speed_data = api.parse_response(name_resp, List[response.CharacterDBModel])
        
        if buffs is None:
            buff_list = None
        else:
            try:
                buff_list = [int(buff) for buff in re.split(r'[,\s]+', buffs) if buff]
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
        language: Optional[Language]=None):  
        '''Shows a character's basic info'''

        char_data = await api.fetch_api(
            api.CHARACTER_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.Character
        )
        try:
            skill_data = await api.fetch_api(
                api.CHARACTER_SKILL_PATH,
                path_params={'char_id': character},
                query_params={'language': language},
                response_model=response.Skills
            )
        except BotError as e:
            skill_data = None  # Case where skill data is not avaliable when basic info is
        
        embed = char_page.char_info_embed(char_data, skill_data)

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
        language: Optional[Language]=None):
        '''Shows character skills including unique weapon upgrade effects'''

        skill_data = await api.fetch_api(
            api.CHARACTER_SKILL_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.Skills
        )

        char_data = await api.fetch_api(
            api.CHARACTER_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.Character
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
        language: Optional[Language]=None):
        '''Shows character skills and details'''

        skill_data = await api.fetch_api(
            api.CHARACTER_SKILL_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.Skills
        )

        char_data = await api.fetch_api(
            api.CHARACTER_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.Character
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
        language: Optional[Language]=None):
        '''Shows character voicelines'''

        # f'{moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{}'

        voice_data = await api.fetch_api(
            api.CHARACTER_VOICE_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.CharacterVoicelines
        )

        profile_data = await api.fetch_api(
            api.CHARACTER_PROFILE_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.Profile
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
        language: Optional[Language]=None):
        '''Shows character memories'''
        memory_data = await api.fetch_api(
            api.CHARACTER_MEMORY_PATH,
            path_params={'char_id': character},
            query_params={'language': language},
            response_model=response.CharacterMemories
        )

        view = await char_page.memory_view(interaction, memory_data, language)
        await show_view(interaction, view)
        
async def setup(bot):
	await bot.add_cog(CharacterCommands(bot))
 