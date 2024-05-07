'''
Main file for the bot
'''
import discord
from discord.ext import commands
import os
import asyncio
import argparse

from dotenv import load_dotenv
from master_data import MasterData
from mementodb import MememoriDB

class AABot(commands.Bot):  # include masterdata in the class
    def __init__(self, command_prefix, intents: discord.Intents, owner_id: int, activity: discord.Activity, log_channel):
        super().__init__(command_prefix=command_prefix, intents=intents, owner_id=owner_id, activity=activity)
        self.masterdata = MasterData()
        self.db = MememoriDB()
        self.log_channel = log_channel
    
    async def on_ready(self):
        await self.wait_until_ready()
        print('AA is online')

async def load():  #load cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main(token):  # code to run the bot
    async with bot:
        await load()
        await bot.start(token)

if __name__ == "__main__":
    # import logging
    # discord.utils.setup_logging(level=logging.DEBUG)
    file_path = os.path.abspath(__file__)  # Get the absolute path of the script
    file_dir = os.path.dirname(file_path)  # Extract the directory
    os.chdir(file_dir)


    
    parser = argparse.ArgumentParser()
    parser.add_argument('--docker_secrets', action='store_true', help='Use when running on a docker container')
    args = parser.parse_args()
    
    discord.utils.setup_logging()
    intents=discord.Intents.default()
    activity = discord.Activity(
        name='you auto click',
        type=discord.ActivityType.watching)
    
    load_dotenv()
    OWNER_ID = int(os.getenv('OWNER_ID'))
    TOKEN = os.getenv('TOKEN')  # test bot token
    LOG_CHANNEL=int(os.getenv('LOG_CHANNEL'))
    
    bot = AABot(command_prefix='!', intents=intents, owner_id=OWNER_ID, activity=activity, log_channel=LOG_CHANNEL)
    
    bot.masterdata.load_all()  # preload main json data before running the bot
    asyncio.run(main(TOKEN))

