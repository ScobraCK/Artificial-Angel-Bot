import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
from typing import Any, List, Optional
from common import raw_asset_link_header


def cog_help_field(name: str, cog: commands.Cog)->dict:  # embed field dict
    cmd_list = cog.get_app_commands()
    value = f"```{', '.join(map(lambda x: x.name, cmd_list))}```"  # join strings
    
    return {'name': name, 'value': value, 'inline': False}

def get_param_text(param: app_commands.Parameter)->str: 
    # main parameter info
    param_text = f"**{param.display_name.title()} ({param.type.name.title()}) "
    if param.required:
        param_text += "[Required]:**\n"
    else:
        param_text += "[Optional]:**\n"

    # description
    param_text += f"{param.description}\n"
    #choices
    if (choices := param.choices):
        param_text += f"Choices: *{', '.join(map(lambda x: x.name, choices))}*\n"
        if (default := param.default) is not MISSING:
            param_text += f"Default: {default}\n"
    return param_text


def command_help_embed(cmd_name: str, cmd: app_commands.Command)->discord.Embed:
    if cmd:
        params = cmd.parameters
        format_text = f"/{cmd_name} "
        param_text = ''
        for param in params:
            if param.required:
                format_text += f"**[{param.display_name}]** "
            else:
                format_text += f"[{param.display_name}] "
            param_text += get_param_text(param)

        embed = discord.Embed(
            title=f"{cmd_name.title()} Command",
            description=f"{cmd.description}\n\n"\
                + f"**Format:** {format_text}\n\n"\
                + f"**Parameters:**\n{param_text}"
        )

    else:
        embed = discord.Embed(
            title='Command Not found',
            description=f'I could not find the command `{cmd_name}`. '
                + f'Check if you spelled it correctly, or if think this is a bug, report in on the suport server. https://discord.gg/DyATxE7saX'
        )
    return embed


class Help(commands.Cog, name='Help Commands'):
    '''Contains the help command'''

    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        command='The command you want more info about'
    )
    async def help(self, interaction: discord.Interaction, command: Optional[str]=None):
        '''See the list of commands and how to use them'''
        if command is None:
            embed = discord.Embed(
                title= "Mertillier's guide to A.A.",
                description="For detailed help for a command, use **/help command**\n"\
                    + "If you find any problems with the bot, join the support server: https://discord.gg/DyATxE7saX"
                )
            for cog in self.bot.cogs:
                if cog == 'Dev Commands' or cog == 'Timer Cog':
                    continue
                embed.add_field(**cog_help_field(cog, self.bot.cogs[cog]))

        else:
            cmd = self.bot.tree.get_command(command)
            embed=command_help_embed(command, cmd)
             
        embed.color = discord.Colour.green()
        (
            embed.set_footer(text='Help command format inspired by Eresh Bot')
                .set_thumbnail(url=raw_asset_link_header + 'Characters/CHR_000029_00_s.png')
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
	await bot.add_cog(Help(bot))
