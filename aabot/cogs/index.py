from io import StringIO
from itertools import batched
from re import split

from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.embeds import BaseEmbed
import aabot.pagination.index
from aabot.pagination.views import ButtonView, show_view
from aabot.pagination.skills import skill_detail_view
from aabot.utils import api
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import apply_user_preferences, arcana_autocomplete, ArcanaOption, ArcanaOptions
# from aabot.utils.error import BotError
from aabot.utils.utils import calc_buff, character_title
from common import schemas
from common.database import SessionAA
from common.enums import LanguageOptions


def speed_view(
    interaction: Interaction,
    char_data: schemas.APIResponse[list[schemas.CharacterDBModel]],
    name_data: schemas.APIResponse[dict[int, schemas.Name]],
    add: int, buffs: list[int]=None):
    speed_list = reversed(char_data.data)

    if add or buffs:
        header = '__No.__ __Character__ __Speed__ __(Base)__\n'
    else:
        header = '__No.__ __Character__ __Speed__\n'

    embeds = []
    i = 1
    for batch in batched(speed_list, 50):
        description = StringIO()
        for char in batch:
            name = name_data.data.get(char.id)
            char_name = character_title(name.title, name.name) if name else '[Undefined]'
            if add or buffs:
                speed = calc_buff(char.speed+add, buffs) if buffs else (char.speed+add)
                description.write(f'**{i}.** {char_name} {speed} ({char.speed})\n')
            else:
                description.write(f'**{i}.** {char_name} {char.speed}\n')
            i += 1

        embed = BaseEmbed(char_data.version, title='Character Speeds', description=f'{header}{description.getvalue()}')
        embed.add_field(
            name='Bonus Parameters',
            value=f'Rune Bonus: {add}\nBuffs: {buffs}',
            inline=False
        )

        embeds.append(embed)

    view = ButtonView(interaction.user, {'default': embeds})
    return view

class IndexCommands(commands.Cog, name='Index Commands'):
    '''Commands for indexing characters and other data.'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
    language='Text Language. Defaults to English.'
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
        view = aabot.pagination.index.id_list_view(interaction, name_data)
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

        view = speed_view(interaction, speed_data, name_data, add, buff_list)
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

        view = await aabot.pagination.index.arcana_view(interaction, arcana_data, self.bot.common_strings[language], language)
        await show_view(interaction, view)




async def setup(bot: AABot):
	await bot.add_cog(IndexCommands(bot))
