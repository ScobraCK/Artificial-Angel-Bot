import asyncio
import os
import traceback

import discord
from discord.ext import commands

from aabot.utils.api import fetch_common_strings
from aabot.utils.error import BotError

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

OWNER_ID = int(os.getenv('OWNER_ID'))
TOKEN = os.getenv('TOKEN')  # test bot token
LOG_CHANNEL=int(os.getenv('LOG_CHANNEL'))
ERROR_CHANNEL=int(os.getenv('ERROR_CHANNEL'))
API_KEY = os.getenv('API_KEY')

async def on_tree_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    err_channel = interaction.client.get_channel(ERROR_CHANNEL)
    data = interaction.data
    command_name = data.get('name')
    options = data.get('options')
    arguments = "\n".join([f"{option.get('name')}: {option.get('value')}" for option in options]) if options else "None"

    if isinstance(error, BotError):
        logger.error(f'{error} - {interaction.data}')
        embed = discord.Embed(
            title="Error",
            description=error.message,
            color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    elif isinstance(error, discord.app_commands.errors.CheckFailure):  # Pass check failures
        logger.error(f'{error} - {interaction.data}')
        await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)
    else:
        logger.error(f'{error} - {interaction.data}', exc_info=True)
        trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if len(trace) > 4000:
            trace = trace[:trace.rfind('\n', 0, 3997)] + "\n..."  # Truncate the trace to 4000 characters
        embed = discord.Embed(
            title=f"/{command_name}",
            description=f"Arguments:\n```{arguments}```\n\nDetails:\n```{trace}```",
            color=discord.Color.red()
        )
        await err_channel.send(embed=embed)
        await interaction.response.send_message(f'An unexpected error occured. Message @habenyan if this persists.', ephemeral=True)

class AABot(commands.Bot):  # include masterdata in the class
    def __init__(self, command_prefix, intents: discord.Intents, owner_id: int, activity: discord.Activity, log_channel, api_key, common_strings):
        super().__init__(command_prefix=command_prefix, intents=intents, owner_id=owner_id, activity=activity)
        self.log_channel = log_channel
        self.api_key = api_key
        self.common_strings = common_strings
        self.tree.on_error = on_tree_error
    
    async def on_ready(self):
        await self.wait_until_ready()
        print('AA is online')

    # async def on_disconnect(self):
    #     pass

async def load(bot):  # load cogs
    for filename in os.listdir('aabot/cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f"aabot.cogs.{filename[:-3]}")

async def main():
    await asyncio.sleep(2)
    intents=discord.Intents.default()
    activity = discord.Activity(
        name='you auto click',
        type=discord.ActivityType.watching)
    common_strings = await fetch_common_strings()
    bot = AABot(command_prefix=commands.when_mentioned_or('!'), intents=intents, owner_id=OWNER_ID, activity=activity, log_channel=LOG_CHANNEL, api_key=API_KEY, common_strings=common_strings)

    async with bot:
        await load(bot)
        await bot.start(TOKEN)

if __name__ == "__main__":
    discord.utils.setup_logging()
    asyncio.run(main())
