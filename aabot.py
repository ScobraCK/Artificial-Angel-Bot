import discord
from discord.ext import commands

import os
import asyncio

import load_env
from master_data import MasterData

class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents: discord.Intents, owner_id: int, activity: discord.Activity):
        super().__init__(command_prefix=command_prefix, intents=intents, owner_id=owner_id, activity=activity)
        self.masterdata = MasterData()
    
    async def on_ready(self):
        await self.wait_until_ready()
        print('AA is online')

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(load_env.TOKEN)

if __name__ == "__main__":
    discord.utils.setup_logging()
    intents=discord.Intents.default()
    intents.message_content = True
    activity = discord.Activity(
        name='you auto click',
        type=discord.ActivityType.watching)
    

    bot = MyBot(command_prefix='!', intents=intents, owner_id=load_env.OWNER_ID, activity=activity)
    bot.masterdata.load_all()
    asyncio.run(main())