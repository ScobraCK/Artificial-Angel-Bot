import os
from dotenv import load_dotenv
import discord

load_dotenv()
MY_GUILD = discord.Object(id=os.getenv('GUILD_ID'))
OWNER_ID = int(os.getenv('OWNER_ID'))
TOKEN = os.getenv('TOKEN2')  # test bot token