from collections import namedtuple
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
from common.database import SessionAA

ArcanaOption = namedtuple('ArcanaOption', ['category', 'type', 'change_type', 'level_bonus'], defaults=(None, None, None, None))

ArcanaOptions = {
    'STR Flat': ArcanaOption('Base', 1, 1),
    'STR Chara. Lv': ArcanaOption('Base', 1, 3),
    'DEX Flat': ArcanaOption('Base', 2, 1),
    'DEX Chara. Lv': ArcanaOption('Base', 2, 3),
    'MAG Flat': ArcanaOption('Base', 3, 1),
    'MAG Chara. Lv': ArcanaOption('Base', 3, 3),
    'STA Flat': ArcanaOption('Base', 4, 1),
    'STA Chara. Lv': ArcanaOption('Base', 4, 3),
    'HP Percent': ArcanaOption('Battle', 1, 2),
    'ATK Flat': ArcanaOption('Battle', 2, 1),
    'ATK Percent': ArcanaOption('Battle', 2, 2),
    'P.DEF Flat': ArcanaOption('Battle', 3, 1),
    'P.DEF Percent': ArcanaOption('Battle', 3, 2),
    'M.DEF Flat': ArcanaOption('Battle', 4, 1),
    'M.DEF Percent': ArcanaOption('Battle', 4, 2),
    'ACC Flat': ArcanaOption('Battle', 5, 1),
    'ACC Percent': ArcanaOption('Battle', 5, 2),
    'ACC Chara. Lv': ArcanaOption('Battle', 5, 3),
    'EVD Flat': ArcanaOption('Battle', 6, 1),
    'EVD Chara. Lv': ArcanaOption('Battle', 6, 3),
    'CRIT Chara. Lv': ArcanaOption('Battle', 7, 3),
    'CRIT RES Flat': ArcanaOption('Battle', 8, 1),
    'CRIT RES Chara. Lv': ArcanaOption('Battle', 8, 3),
    'CRIT DMG Boost Flat': ArcanaOption('Battle', 9, 1),
    'P.CRIT DMG Cut Flat': ArcanaOption('Battle', 10, 1),
    'M.CRIT DMG Cut Flat': ArcanaOption('Battle', 11, 1),
    'DEF Break Flat': ArcanaOption('Battle', 12, 1),
    'DEF Percent': ArcanaOption('Battle', 13, 2),
    'DEF Chara. Lv': ArcanaOption('Battle', 13, 3),
    'PM.DEF Break Flat': ArcanaOption('Battle', 14, 1),
    'Debuff ACC Percent': ArcanaOption('Battle', 15, 2),
    'Debuff ACC Chara. Lv': ArcanaOption('Battle', 15, 3),
    'Debuff RES Flat': ArcanaOption('Battle', 16, 1),
    'Debuff RES Chara. Lv': ArcanaOption('Battle', 16, 3),
    'Counter Flat': ArcanaOption('Battle', 17, 1),
    'HP Drain Flat': ArcanaOption('Battle', 18, 1),
    'Level Bonus': ArcanaOption(None, None, None, True)
}

async def arcana_autocomplete(interaction: Interaction, current: str):
    choices = [
        app_commands.Choice(name=opt, value=opt)
        for opt in ArcanaOptions
        if current.replace('.', '').lower() in opt.replace('.', '').lower()
    ]
    return choices[:25]


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
        async with SessionAA() as session:
            view = await skill_detail_view(interaction, skill_data, char_data, session)
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
        character='Character filter option',
        filter_option='Filter options for arcana bonus',
        language='Text language. Defaults to English.'
    )
    @app_commands.autocomplete(filter_option=arcana_autocomplete)
    @apply_user_preferences()
    async def arcana(
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

            options = ArcanaOptions[filter_option]
        else:
            options = ArcanaOption()

        arcana_data = await api.fetch_api(
            api.ARCANA_PATH,
            response_model=list[schemas.Arcana],
            query_params={
                'character': character,
                'param_category': options.category,
                'param_type': options.type,
                'param_change_type': options.change_type,
                'level_bonus': options.level_bonus,
                'language': language
            }
        )

        view = await char_page.arcana_view(interaction, arcana_data, self.bot.common_strings[language], language)
        await show_view(interaction, view)


async def setup(bot: AABot):
	await bot.add_cog(CharacterCommands(bot))
