import datetime, time, sqlite3
import requests, json
from discord.ext import commands, tasks

utc = datetime.timezone.utc

# If no tzinfo is given then UTC is assumed.
cur_time = datetime.time(hour=13, tzinfo=utc)

class GuildDB():  # need to move out of cog
    def __init__(self) -> None:
        self.con = sqlite3.connect('guild.db')
        self.cur = self.con.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            id varchar(12) PRIMARY KEY,
            name text,
            bp int,
            level int,
            world int,
            server int)
        """)

    def insert_guilds(self, guilds: dict, server: int, world: int, ):
        for guild in guilds:
            guild['world'] = world
            guild['server'] = server
            self.cur.execute("INSERT OR REPLACE INTO guilds (id, name, bp, level, world, server)"
                             "VALUES (:id, :name, :bp, :level, :world, :server)",
                             guild)
        self.con.commit()

    def get_server_ranking(self, server):
        res = self.cur.execute(
            "SELECT name, bp, level, world FROM guilds WHERE server = (?) ORDER BY bp DESC", (server, )
        )
        return res.fetchmany(100)
    
    def close(self):
        self.con.close()

def fetch_guildlist(server: int, world: int):
    world_id = f"{server}{world:03}"
    url = f"https://api.mentemori.icu/{world_id}/guild_ranking/latest"
    resp = requests.get(url)
    data = json.loads(resp.content.decode('utf-8'))

    return data

def fetch_worlddata():
    url = f"https://api.mentemori.icu/worlds"
    resp = requests.get(url)
    data = json.loads(resp.content.decode('utf-8'))

    return data['data']  # need error checks

class TimerCog(commands.Cog, name = 'Timer Cog'):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()
        self.bot.block_guilddb = False

    def cog_unload(self):
        self.my_task.cancel()

    def cog_load(self):  # temporary measure to initiate
        self.bot.block_guilddb = True
        time.sleep(1)  # in case there is other use, need further error checking implemented

        db = GuildDB()
        worlds = fetch_worlddata()
        for world_data in worlds:
            server = int(str(world_data['world_id'])[0])
            world = int(str(world_data['world_id'])[1:])

            if world_data['ranking'] == False:
                continue

            data = fetch_guildlist(server, world)
            if data['status'] != 200:
                continue
            print(world_data['world_id'])
            guilds = data['data']['rankings']['bp']
            db.insert_guilds(guilds, server, world)

        db.close()
        self.bot.block_guilddb = False

    @tasks.loop(time=cur_time)
    async def my_task(self):
        self.bot.block_guilddb = True
        time.sleep(1)  # in case there is other use, need further error checking implemented

        db = GuildDB()
        worlds = fetch_worlddata()
        for world_data in worlds:
            server = int(str(world_data['world_id'])[0])
            world = int(str(world_data['world_id'])[1:])

            if world_data['ranking'] == False:
                continue

            data = fetch_guildlist(server, world)
            if data['status'] != 200:
                continue
            
            guilds = data['data']['rankings']['bp']
            db.insert_guilds(guilds, server, world)

        db.close()
        self.bot.block_guilddb = False

     
async def setup(bot):
	await bot.add_cog(TimerCog(bot))