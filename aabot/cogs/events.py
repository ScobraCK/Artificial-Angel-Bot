from discord import app_commands, Interaction
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination import events as event_page
from aabot.utils import api, assets
from aabot.utils.alias import IdTransformer
from aabot.utils.command_utils import LanguageOptions
from common import schemas

class EventCommands(commands.Cog, name='Event Commands'):
    '''Commands for game events'''

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
        gacha_data = await api.fetch_api(
            api.GACHA_PATH,
            response_model=schemas.GachaBanners,
            query_params={
                'include_future': True
            }
        )
        embed = await event_page.gacha_banner_embed(gacha_data, language)
        
        await interaction.response.send_message(embed=embed)
    
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
        gacha_data = await api.fetch_api(
            api.GACHA_PATH,
            response_model=schemas.GachaBanners,
            query_params={
                'char_id': character,
                'is_active': False
            }
        )
        embed = await event_page.gacha_banner_embed(gacha_data, language)
        embed.set_thumbnail(url=assets.CHARACTER_THUMBNAIL.format(char_id=character, qlipha=False))
        await interaction.response.send_message(embed=embed)

async def setup(bot: AABot):
	await bot.add_cog(EventCommands(bot))