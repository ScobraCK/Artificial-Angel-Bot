from discord import app_commands, Interaction, Embed
from discord.ext import commands

from aabot.crud.user import update_user, get_user, delete_user
from aabot.main import AABot
from aabot.utils.utils import possessive_form
from aabot.utils.command_utils import LanguageOptions
from common.database import AsyncSession as SessionAABot
from common.enums import Server
from common.models import UserPreference

def user_embed(user: UserPreference, name: str):
    embed = Embed(
        title = f'{possessive_form(name)} Settings',
        description=(
            f'**Language:** {user.language}\n'
            f'**Server:** {user.server}\n'
            f'**World:** {user.world}'
        ) if user else 'No preference set.',
    ).set_footer(text='You can always change preference settings using /setpreference or delete your data using /deletepreference')

    return embed

class UserCommands(commands.Cog, name='User Commands'):
    '''User Preference'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
        language='Preferred language setting.',
        server='Preferred server setting.',
        world='Preferred world setting.',
    )
    async def setpreference(
        self,
        interaction: Interaction,
        language: LanguageOptions|None,
        server: Server|None,
        world: int|None
    ):
        '''Sets a default input for language, server, and world settings when applicable. Ranking commands do not use preference data.'''
        async with SessionAABot() as session:
            user = await update_user(session, interaction.user.id, language, server, world)
            embed = user_embed(user, interaction.user.display_name)

            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def preference(
        self,
        interaction: Interaction
    ):
        '''View current preference setting. Ranking commands do not use preference data.'''
        async with SessionAABot() as session:
            user = await get_user(session, interaction.user.id)
            name = interaction.user.display_name
            embed = user_embed(user, name)
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def deletepreference(
        self,
        interaction: Interaction
    ):
        '''Deletes preference data.'''
        async with SessionAABot() as session:
            result = await delete_user(session, interaction.user.id)
            if result:
                await interaction.response.send_message('Successfully deleted preference data.')
            else:
                await interaction.response.send_message('Preference data did not exist.')
        

async def setup(bot: AABot):
	await bot.add_cog(UserCommands(bot))