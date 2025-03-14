from discord.ext import commands, tasks
from zoneinfo import ZoneInfo
from datetime import time

from aabot.api import api
from aabot.main import AABot
from aabot.utils.error import BotError
from aabot.utils.timezones import get_cur_timestr_KR

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
        msg = f'**Auto Update**\n{get_cur_timestr_KR()}\n'
        try:
            await api.fetch(api.UPDATE_API_GUILD_PATH, base_url=api.API_BASE_PATH, params={'key': self.bot.api_key}, timeout=30)
            await api.fetch(api.UPDATE_API_PLAYERS_PATH, base_url=api.API_BASE_PATH, params={'key': self.bot.api_key}, timeout=30)
            msg += 'Updated player and guild rankings'
        except BotError as e:
            msg += f'Update failed <@{self.bot.owner_id}>\n{e.message}'
 
        await ch.send(msg)
             
    @update_ranking.before_loop
    async def before_update_ranking(self):
        await self.bot.wait_until_ready()         
             
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        