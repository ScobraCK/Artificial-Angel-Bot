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
        msg1 = f'{get_cur_time()}\n{res1}'
        embed1 = discord.Embed(description=msg1)
        if status1:
            await ch.send(embed=embed)
        else:
            embed1.description = f'{msg1}\n<@395172008150958101>'
            await ch.send(embed=embed1)

        res2, status2 = update_player_rankings(self.bot.db)
        msg2 = f'{get_cur_time()}\n{res2}'
        embed = discord.Embed(description=msg2)
        if status2:
            await ch.send(embed=embed)
        else:
            embed.description = f'{msg2}\n<@395172008150958101>'
            await ch.send(embed=embed)
             
     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        