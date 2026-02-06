from discord import app_commands, Interaction, ui
from discord.ext import commands

from aabot.crud.user import update_user, get_user, delete_user
from aabot.pagination.view import BaseView, BaseContainer
from aabot.main import AABot
from aabot.utils.utils import possessive_form
from common.database import SessionAA
from common.enums import LanguageOptions, Server
from common.models import UserPreference

def user_ui(user: UserPreference, name: str) -> BaseContainer:
    container = (
        BaseContainer(f'### {possessive_form(name)} Settings')
        .add_item(
            ui.TextDisplay(
                f'**Language:** {user.language}\n'
                f'**Server:** {user.server}\n'
                f'**World:** {user.world}'
            ) if user else ui.TextDisplay('No preference set.')
        ).add_item(
            ui.TextDisplay('-# You can always change preference settings using /setpreference or delete your data using /deletepreference')
        )
    )
    return container

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
        async with SessionAA() as session:
            user = await update_user(session, interaction.user.id, language, server, world)
        view = BaseView(user_ui(user, interaction.user.display_name), interaction.user)
        await view.update_view(interaction)
    @app_commands.command()
    async def preference(
        self,
        interaction: Interaction
    ):
        '''View current preference setting. Ranking commands do not use preference data.'''
        async with SessionAA() as session:
            user = await get_user(session, interaction.user.id)
        view = BaseView(user_ui(user, interaction.user.display_name), interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    async def deletepreference(
        self,
        interaction: Interaction
    ):
        '''Deletes preference data.'''
        async with SessionAA() as session:
            result = await delete_user(session, interaction.user.id)
            if result:
                await interaction.response.send_message('Successfully deleted preference data.', ephemeral=True)
            else:
                await interaction.response.send_message('Preference data did not exist.', ephemeral=True)
        

async def setup(bot: AABot):
	await bot.add_cog(UserCommands(bot))