import sqlite3, requests, json
from dataclasses import dataclass

@dataclass
class GuildData():
    world: int
    bp: int
    name: str
    level: int

    def list_bp(self):
        return [self.bp, self.world, self.name]

class GuildDB():
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

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS worlds (
            world_id int PRIMARY KEY,
            group_id int,
            world int,
            server int)
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id int PRIMARY KEY,
            server int,
            start int,
            end int)
        """)

    def update_group(self, group_data):
        for group in group_data:
            group_id = group['Id']
            server = group['TimeServerId']
            world_list = []
            for world_id in group['WorldIdList']:
                world = world_id % 1000
                world_list.append(world)
                # add to worlds
                self.cur.execute(
                    "INSERT OR REPLACE INTO worlds (world_id, group_id, world, server) VALUES (?, ?, ?, ?)",
                    (world_id, group_id, world, server))
            # add to groups
            self.cur.execute(
                    "INSERT OR REPLACE INTO groups (group_id, server, start, end) VALUES (?, ?, ?, ?)",
                    (group_id, server, world_list[0], world_list[-1]))
        self.con.commit()

    def get_group_list(self, server):
        res = self.cur.execute(
            "SELECT group_id, start, end FROM groups where server = (?)", (server, )
        )
        return res.fetchall()
    
    def get_world_list(self, group):
        res = self.cur.execute(
            "SELECT world FROM worlds where group_id = (?)", (group, )
        )
        worlds = res.fetchall()
        return [id[0] for id in worlds]

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
            "SELECT bp, world, name FROM guilds WHERE server = (?) ORDER BY bp DESC", (server, )
        )
        return res.fetchmany(200)
    
    def get_group_ranking(self, server, group_id):
        world_list = self.get_world_list(group_id)
        query = f"SELECT bp, world, name FROM guilds WHERE server = (?) AND world in ({','.join(['?']*len(world_list))}) ORDER BY bp DESC"
        res = self.cur.execute(
            query, tuple([server] + world_list)
        )
        return res.fetchmany(50)
    
    def get_group_id(self, server, world):
        res = self.cur.execute(
            "SELECT group_id from worlds WHERE server = (?) AND world = (?)", (server, world)
        )
        return res.fetchone()
    
    def get_group_worlds(self, group_id):
        res = self.cur.execute(
            "SELECT start, end from groups WHERE group_id = (?)", (group_id, )
        )
        return res.fetchone()
    
    def close(self):
        self.con.close()

def fetch_guildlist(server: int, world: int):
    world_id = f"{server}{world:03}"
    url = f"https://api.mentemori.icu/{world_id}/guild_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data
    else:
        return None

def fetch_worlddata():
    url = f"https://api.mentemori.icu/worlds"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data['data']  # need error checks
    else:
        return None

def fetch_group_list(server):
    db = GuildDB()
    data = db.get_group_list(server)
    db.close()
    return data
