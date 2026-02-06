from discord import Interaction, app_commands
from discord.ext import commands

from aabot.main import AABot
from aabot.pagination.help import command_help_ui, default_help_ui
from aabot.pagination.view import BaseContainer, BaseView


class HelpCommands(commands.Cog, name='Help Commands'):
    '''Contains the help command'''

    def __init__(self, bot):
        self.bot: AABot = bot
    
    @app_commands.command()
    @app_commands.describe(
        command='The command you want more info about'
    )
    async def help(self, interaction: Interaction, command: str|None=None):
        '''See the list of commands and how to use them'''
        if command is None:
            content = default_help_ui(self.bot.cogs)
        else:
            cmd = self.bot.tree.get_command(command)
            if not cmd:
                content = BaseContainer(f'Could not find the command `{command}`.')
            else:
                content = command_help_ui(cmd)
             
        view = BaseView(content, interaction.user)
        await view.update_view(interaction)

async def setup(bot: AABot):
	await bot.add_cog(HelpCommands(bot))



