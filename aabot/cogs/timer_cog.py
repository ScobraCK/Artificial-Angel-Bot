import datetime, discord
from discord.ext import commands, tasks

from mementodb import async_update_guild_rankings, async_update_player_rankings, update_guild_rankings, update_player_rankings
from timezones import get_cur_time
from main import AABot

# utc = datetime.timezone.utc

# # If no tzinfo is given then UTC is assumed.
# cur_time = datetime.time(hour=13, tzinfo=utc)

class TimerCog(commands.Cog, name = 'Timer Cog'):
    def __init__(self, bot: AABot):
        self.bot = bot
        
    async def cog_load(self):
        self.update_ranking.start()

    async def cog_unload(self):
        self.update_ranking.cancel()

    @tasks.loop(hours=4)
    async def update_ranking(self):
        ch = self.bot.get_channel(self.bot.log_channel)
        
        res1, status1 = update_guild_rankings(self.bot.db)
        res2, status2 = update_player_rankings(self.bot.db)
        
        # res1, status1 = await async_update_guild_rankings(self.bot.db)
        # res2, status2 = await async_update_player_rankings(self.bot.db)
        
        msg = f'**Auto Update**\n{get_cur_time()}\n{res1}\n{res2}'

        if status1 and status2:
            await ch.send(msg)
        else:
            msg = f'{msg}\n<@{self.bot.owner_id}>'
            await ch.send(msg)
             
    @update_ranking.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()         
             
     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        