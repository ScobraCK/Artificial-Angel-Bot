import sqlite3, requests, json
from typing import List
from dataclasses import dataclass

@dataclass
class GuildData():
    world: int
    bp: int
    name: str

    def list_bp(self):
        return [self.bp, self.world, self.name]

class MememoriDB():
    def __init__(self) -> None:
        self.con = sqlite3.connect('ranking.db')
        self.cur = self.con.cursor()
        
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            id varchar(12) PRIMARY KEY,
            name text,
            bp int,
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

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id int PRIMARY KEY,
            server int,
            world int,
            name int,
            bp int,
            rank int,
            quest int,
            tower int)
        """)

    # INSERT

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

    def insert_guilds(self, guilds: List[dict], server: int, world: int):
        for guild in guilds:
            guild['world'] = world
            guild['server'] = server
            self.cur.execute("INSERT OR REPLACE INTO guilds (id, name, bp, world, server)"
                             "VALUES (:id, :name, :bp, :world, :server)",
                             guild)
        self.con.commit()

    def update_players(self, server, world, rankings):
        # update bp + name update
        for player in rankings['bp']:
            self.cur.execute("INSERT OR REPLACE INTO players (id, server, world, name, bp)"
                            "VALUES (?, ?, ?, ?, ?)"
                            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, bp=excluded.bp",
                            (player['id'], server, world, player['name'], player['bp']))
        # update rank
        for player in rankings['rank']:
            self.cur.execute("INSERT OR REPLACE INTO players (id, server, world, name, rank)"
                            "VALUES (?, ?, ?, ?, ?)"
                            "ON CONFLICT(id) DO UPDATE SET rank=excluded.rank",
                            (player['id'], server, world, player['name'], player['rank']))
        # update quest
        for player in rankings['quest']:
            self.cur.execute("INSERT OR REPLACE INTO players (id, server, world, name, quest)"
                            "VALUES (?, ?, ?, ?, ?)"
                            "ON CONFLICT(id) DO UPDATE SET quest=excluded.quest",
                            (player['id'], server, world, player['name'], player['quest_id']))
        # update tower
        for player in rankings['tower']:
            self.cur.execute("INSERT OR REPLACE INTO players (id, server, world, name, tower)"
                            "VALUES (?, ?, ?, ?, ?)"
                            "ON CONFLICT(id) DO UPDATE SET tower=excluded.tower",
                            (player['id'], server, world, player['name'], player['tower_id']))
        
        self.con.commit()
    
    # READ
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
    
    def get_server_guild_ranking(self, server):
        res = self.cur.execute(
            "SELECT bp, world, name FROM guilds WHERE server = (?) ORDER BY bp DESC", (server, )
        )
        return res.fetchmany(200)
    
    def get_group_guild_ranking(self, server, group_id):
        world_list = self.get_world_list(group_id)
        query = f"SELECT bp, world, name FROM guilds WHERE server = (?) AND world in ({','.join(['?']*len(world_list))}) ORDER BY bp DESC"
        res = self.cur.execute(
            query, tuple([server] + world_list)
        )
        return res.fetchmany(50)
    
    def get_server_player_ranking(self, server, order='bp'):
        '''order can be bp, quest'''
        res = self.cur.execute(
            f"SELECT world, bp, quest, name FROM players WHERE server = (?) ORDER BY {order} DESC", (server, )
        )
        return res.fetchmany(200)        
    
    def get_all_player_ranking(self, order='bp'):
        '''
        order can be bp, quest
        None defaults to bp
        '''
        res = self.cur.execute(
            f"SELECT server, world, bp, quest, name FROM players ORDER BY {order} DESC"
        )
        return res.fetchmany(500)

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
    
def fetch_guildlist_all():
    url = f"https://api.mentemori.icu/0/guild_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data['data']
    else:
        return None
    
def fetch_player_ranking_all():
    url = f"https://api.mentemori.icu/0/player_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data['data']
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
    db = MememoriDB()
    data = db.get_group_list(server)
    db.close()
    return data

def update_guild_rankings(gdb: MememoriDB):
    guild_data = fetch_guildlist_all()
    if guild_data:
        try:
            for data in guild_data:
                world_id = str(data['world_id'])
                server = int(world_id[0])
                world = int(world_id[1:])
                guilds = data['rankings']['bp']
                gdb.insert_guilds(guilds, server, world)
            return "Updated guild rankings", True
        except Exception as e:
            return e, False
    else:
        return 'API fail', False

def update_player_rankings(gdb: MememoriDB):
    player_data = fetch_player_ranking_all()
    if player_data:
        try:
            for data in player_data:
                world_id = str(data['world_id'])
                server = int(world_id[0])
                world = int(world_id[1:])
                rankings = data['rankings']
                gdb.update_players(server, world, rankings)
            return "Updated player rankings", True
        except Exception as e:
            return e, False
    else:
        return 'API fail', False
