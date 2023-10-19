'''
Main file for the bot
'''
import discord
from discord.ext import commands
import os
import asyncio

import load_env
from master_data import MasterData
from guilddb import GuildDB

class AABot(commands.Bot):  # include masterdata in the class
    def __init__(self, command_prefix, intents: discord.Intents, owner_id: int, activity: discord.Activity):
        super().__init__(command_prefix=command_prefix, intents=intents, owner_id=owner_id, activity=activity)
        self.masterdata = MasterData()
        self.gdb = GuildDB()
    
    async def on_ready(self):
        await self.wait_until_ready()
        print('AA is online')

async def load():  #load cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():  # code to run the bot
    async with bot:
        await load()
        await bot.start(load_env.TOKEN)

if __name__ == "__main__":
    # import logging
    # discord.utils.setup_logging(level=logging.DEBUG)
    discord.utils.setup_logging()
    intents=discord.Intents.default()
    intents.message_content = True
    activity = discord.Activity(
        name='you auto click',
        type=discord.ActivityType.watching)
    
    bot = AABot(command_prefix='!', intents=intents, owner_id=load_env.OWNER_ID, activity=activity)
    bot.masterdata.load_all()  # preload main json data before running the bot
    asyncio.run(main())