import os
from dotenv import load_dotenv
import discord

load_dotenv()
MY_GUILD = discord.Object(id=os.getenv('GUILD_ID'))
OWNER_ID = int(os.getenv('OWNER_ID'))
TOKEN = os.getenv('TOKEN')  # test bot token
LOG_CHANNEL=int(os.getenv('LOG_CHANNEL'))