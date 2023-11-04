import datetime, discord
from discord.ext import commands, tasks

from rankingdb import update_guild_rankings, update_player_rankings
from load_env import LOG_CHANNEL
from timezones import get_cur_time
from main import AABot

utc = datetime.timezone.utc

# If no tzinfo is given then UTC is assumed.
cur_time = datetime.time(hour=13, tzinfo=utc)

class TimerCog(commands.Cog, name = 'Timer Cog'):
    def __init__(self, bot: AABot):
        self.bot = bot
        self.my_task.start()

    async def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(time=cur_time)
    async def my_task(self):
        ch = self.bot.get_channel(LOG_CHANNEL)

        res1, status1 = update_guild_rankings(self.bot.db)
        res2, status2 = update_player_rankings(self.bot.db)
        
        msg = f'{get_cur_time()}\n{res1}\n{res2}'

        if status1 and status2:
            await ch.send(msg)
        else:
            msg = f'{msg}\n<@395172008150958101>'
            await ch.send(msg)

             
     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        