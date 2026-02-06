from io import StringIO
from typing import Mapping

from discord import app_commands, ui
from discord.ext import commands
from discord.utils import MISSING

from aabot.pagination.view import BaseContainer

EXCLUDE_COGS = ['Admin Commands', 'Cog Commands', 'Timer Cog']

def get_param_text(param: app_commands.Parameter)->str: 
    # main parameter info
    param_text = f'- **{param.display_name}** ({param.type.name.title()}) '
    if param.required:
        param_text += '[Required]:\n'
    else:
        param_text += '[Optional]:\n'

    # description
    param_text += f'{param.description}\n'
    #choices
    if (choices := param.choices):
        param_text += f'Choices: *{', '.join(map(lambda x: x.name, choices))}*\n'
        if (default := param.default) is not MISSING:
            param_text += f'Default: {default}\n'
    return param_text

def get_help_text(cmd: app_commands.Command) -> str:
    text = StringIO()
    param_buffer = StringIO()
    text.write(f'{cmd.description}\n\n**Format:** `/{cmd.name}')
    for param in cmd.parameters:
        if param.required:
            text.write(f' **[{param.display_name}]**')
        else:
            text.write(f' [{param.display_name}]')
        param_buffer.write(f'{get_param_text(param)}')
    text.write(f'`\n**Parameters:**\n{param_buffer.getvalue()}')
    return text.getvalue()

def command_help_ui(cmd: app_commands.Command) -> BaseContainer:
    container = (
        BaseContainer()
        .add_item(ui.TextDisplay(f'## {cmd.name.title()} Command'))
        .add_item(ui.TextDisplay(get_help_text(cmd)))
    )

    if cmd.extras.get('help'):
        container.add_item(ui.Separator()).add_item(ui.TextDisplay(f'\n{cmd.extras["help"]()}'))

    return container

def default_help_ui(cogs: Mapping[str, commands.Cog]) -> BaseContainer:
    container = BaseContainer().add_item(
        ui.TextDisplay(
            "## Mertillier's guide to A.A.\n"
            "For detailed help for a command, use `/help [command]`\n"
            "If you find any problems with the bot, join the [support server](https://discord.gg/DyATxE7saX).\n"
        )
    )

    for name, cog in cogs.items():
        if name in EXCLUDE_COGS:
            continue
        cmd_list = cog.get_app_commands()
        cmd_names = ', '.join(map(lambda x: x.name, cmd_list))
        container.add_item(
            ui.TextDisplay(f'**{name}**\n```{cmd_names}```')
        )

    return container