from discord.ext import commands, tasks
from zoneinfo import ZoneInfo
from datetime import time

from mementodb import async_update_guild_rankings, async_update_player_rankings, update_guild_rankings, update_player_rankings
from timezones import get_cur_timestr_KR
from main import AABot



class TimerCog(commands.Cog, name = 'Timer Cog'):
    def __init__(self, bot: AABot):
        self.bot = bot
        
    async def cog_load(self):
        self.update_ranking.start()
        self.update_master.start()

    async def cog_unload(self):
        self.update_ranking.cancel()
        self.update_master.cancel()
        
    @tasks.loop(minutes=30)
    async def update_master(self):
        ch = self.bot.get_channel(self.bot.log_channel)
        if self.bot.masterdata.version != self.bot.masterdata.get_version():
            try:
                group_data_old = self.bot.masterdata.get_MB_data('WorldGroupMB')
                self.bot.masterdata.reload_all()
                group_data_new = self.bot.masterdata.get_MB_data('WorldGroupMB')
                
                msg = f'**Auto Update**\nUpdated master data\nVersion: {self.bot.masterdata.version}'
                if group_data_old != group_data_new:
                    self.bot.db.update_groups(group_data_new)
                    msg += '\nUpdated Groups'
                await ch.send(msg)  
            except Exception as e:
                await ch.send(f'**Auto Update Failed**\nFailed during master update\n{e}')  
    
    @update_master.before_loop
    async def before_update_master(self):
        await self.bot.wait_until_ready()      
    
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
        
        res1, timestamp1 = update_guild_rankings(self.bot.db)
        res2, timestamp2 = update_player_rankings(self.bot.db)
        
        msg = f'**Auto Update**\n{get_cur_timestr_KR()}\n{res1} - {timestamp1}\n{res2} - {timestamp2}'

        if timestamp1 == None or timestamp2 == None:  # error
            msg += f'\n<@{self.bot.owner_id}>'
            await ch.send(msg)
        else:  # normal
            await ch.send(msg)
             
    @update_ranking.before_loop
    async def before_update_ranking(self):
        await self.bot.wait_until_ready()         
             
     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        