import datetime, discord
from discord.ext import commands, tasks

from guilddb import update_rankings
from load_env import LOG_CHANNEL
from timezones import get_cur_time

utc = datetime.timezone.utc

# If no tzinfo is given then UTC is assumed.
cur_time = datetime.time(hour=13, tzinfo=utc)

class TimerCog(commands.Cog, name = 'Timer Cog'):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()
        self.bot.block_guilddb = False

    async def cog_unload(self):
        self.my_task.cancel()

    # async def cog_load(self):  # temporary measure to initiate
    #     self.bot.block_guilddb = True
    #     time.sleep(1)  # in case there is other use, need further error checking implemented

    #     db = GuildDB()
    #     worlds = fetch_worlddata()
    #     for world_data in worlds:
    #         server = int(str(world_data['world_id'])[0])
    #         world = int(str(world_data['world_id'])[1:])

    #         if world_data['ranking'] == False:
    #             continue

    #         data = fetch_guildlist(server, world)
    #         if data['status'] != 200:
    #             continue
    #         print(world_data['world_id'])
    #         guilds = data['data']['rankings']['bp']
    #         db.insert_guilds(guilds, server, world)

    #     db.close()
    #     self.bot.block_guilddb = False

    @tasks.loop(time=cur_time)
    async def my_task(self):
        ch = self.bot.get_channel(LOG_CHANNEL)
        msg = get_cur_time() + '\n'
        msg += update_rankings(self.bot.gdb) 
        embed = discord.Embed(description=msg)

        await ch.send(embed=embed)
     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        