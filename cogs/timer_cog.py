import datetime, time, sqlite3
import requests, json
from discord.ext import commands, tasks
from guilddb import fetch_guildlist, fetch_worlddata

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
        time.sleep(1)  # in case there is other use, need further error checking implemented

        worlds = fetch_worlddata()
        if worlds:
            for world_data in worlds:
                server = int(str(world_data['world_id'])[0])
                world = int(str(world_data['world_id'])[1:])

                if world_data['ranking'] == False:
                    continue

                data = fetch_guildlist(server, world)
                if not data:
                    continue
                
                guilds = data['data']['rankings']['bp']
                self.gdb.insert_guilds(guilds, server, world)
     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))
        