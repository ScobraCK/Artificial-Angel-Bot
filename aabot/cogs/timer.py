from datetime import time
from zoneinfo import ZoneInfo

from discord.ext import commands, tasks

from aabot.main import AABot
from aabot.utils import api
from aabot.utils.error import BotError
from common.timezones import get_current

class TimerCog(commands.Cog, name = 'Timer Cog'):
    def __init__(self, bot: AABot):
        self.bot = bot
        
    async def cog_load(self):
        self.update_ranking.start()

    async def cog_unload(self):
        self.update_ranking.cancel() 
    
    @tasks.loop(
        time=[time(hour=0, tzinfo=ZoneInfo("UTC")),
              time(hour=4, tzinfo=ZoneInfo("UTC")),
              time(hour=8, tzinfo=ZoneInfo("UTC")),
              time(hour=12, tzinfo=ZoneInfo("UTC")),
              time(hour=16, tzinfo=ZoneInfo("UTC")),
              time(hour=20, tzinfo=ZoneInfo("UTC"))]
    )
    async def update_ranking(self):
        ch = self.bot.get_channel(self.bot.log_channel)
        msg = f'**Auto Update**\n<t:{get_current()}:f>\n'
        try:
            await api.fetch(api.UPDATE_API_GUILD_PATH, base_url=api.API_BASE_PATH, params={'key': self.bot.api_key}, timeout=30)
            await api.fetch(api.UPDATE_API_PLAYERS_PATH, base_url=api.API_BASE_PATH, params={'key': self.bot.api_key}, timeout=30)
            
        except BotError as e:
            msg += f'Failed to update player and guild rankings\n<@{self.bot.owner_id}>\n{e.message}'
            await ch.send(msg)
             
    @update_ranking.before_loop
    async def before_update_ranking(self):
        await self.bot.wait_until_ready()         
             
async def setup(bot: AABot):
	await bot.add_cog(TimerCog(bot))
        