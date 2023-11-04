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
        self.con = sqlite3.connect('memento.db')
        self.cur = self.con.cursor()
        
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
                         id varchar(12) PRIMARY KEY,          
                         server int,           
                         world int,
                         name text,           
                         bp int,
                         level int,
                         stock int,
                         exp int,
                         num_members int,
                         leader_id int,
                         policy int,
                         description text,
                         free_join int,
                         bp_requirement int,
                         timestamp datetime
            )
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
                         id varchar(12) PRIMARY KEY,
                         server int,
                         world int,
                         name text,
                         bp int,
                         rank int,
                         quest_id int,
                         tower_id int,
                         icon_id int,
                         guild_id int,
                         guild_join_time int,
                         guild_position int,
                         prev_legend_league_class int,
                         timestamp datetime
            )
        """)
        # 1 = Master, 2 = Chief, 3 = Member
        # 1 = Chevalier, 2 = Paladin, 3 = Grand Cross, 4 = Royal Rank, 5 = Legend Rank, 6 = World Ruler

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

    def _insert_guild(self, server, world, guild_data, timestamp):
        # does not commit
        guild_data['server'] = server
        guild_data['world'] = world
        guild_data['timestamp'] = timestamp
        self.cur.execute(
            "INSERT OR REPLACE INTO guilds"
            "(id, server, world, name, bp, level, stock, exp, num_members, leader_id, policy, description, free_join, bp_requirement, timestamp)"
            "VALUES (:id, :server, :world, :name, :bp, :level, :stock, :exp, :num_members, :leader_id, :policy, :description, :free_join, :bp_requirement, :timestamp)",
            guild_data)

    def update_guilds(self, server, world, guild_info: dict, timestamp):
        for guild_data in guild_info.values():
            self._insert_guild(server, world, guild_data, timestamp)
        self.con.commit()

    def _insert_player(self, server, world, player_data, timestamp):
        # does not commit
        player_data['server'] = server
        player_data['world'] = world
        player_data['timestamp'] = timestamp
        self.cur.execute(
            "INSERT OR REPLACE INTO players"
            "(id, server, world, name, bp, rank, quest_id, tower_id, icon_id, guild_id, guild_join_time, guild_position, prev_legend_league_class, timestamp)"
            "VALUES (:id, :server, :world, :name, :bp, :rank, :quest_id, :tower_id, :icon_id, :guild_id, :guild_join_time, :guild_position, :prev_legend_league_class, :timestamp)",
            player_data)

    def update_players(self, server, world, player_info: dict, timestamp):
        for player_data in player_info.values():
            self._insert_player(server, world, player_data, timestamp)
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
            f"SELECT world, bp, quest_id, name FROM players WHERE server = (?) ORDER BY {order} DESC", (server, )
        )
        return res.fetchmany(200)        
    
    def get_all_player_ranking(self, order='bp'):
        '''
        order can be bp, quest
        None defaults to bp
        '''
        res = self.cur.execute(
            f"SELECT server, world, bp, quest_id, name FROM players ORDER BY {order} DESC"
        )
        return res.fetchmany(500)

    def close(self):
        self.con.close()

# UNUSED
def fetch_guildlist(server: int, world: int):
    world_id = f"{server}{world:03}"
    url = f"https://api.mentemori.icu/{world_id}/guild_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data
    else:
        return None
    
def fetch_guilds():
    url = f"https://api.mentemori.icu/0/guild_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data['data'], data['timestamp']
    else:
        return None
    
def fetch_players():
    url = f"https://api.mentemori.icu/0/player_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data['data'], data['timestamp']
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

def split_world_id(world_id):
    world_id = str(world_id)
    return int(world_id[0]), int(world_id[1:])

def update_guild_rankings(gdb: MememoriDB):
    guild_data, timestamp = fetch_guilds()
    if guild_data:
        try:
            for data in guild_data:
                server, world = split_world_id(data['world_id'])
                guilds = data['guild_info']
                gdb.update_guilds(server, world, guilds, timestamp)
            return "Updated guild rankings", True
        except Exception as e:
            return e, False
    else:
        return 'API fail', False

def update_player_rankings(gdb: MememoriDB):
    player_data, timestamp = fetch_players()
    if player_data:
        try:
            for data in player_data:
                server, world = split_world_id(data['world_id'])
                player_info = data['player_info']
                gdb.update_players(server, world, player_info, timestamp)
            return "Updated player rankings", True
        except Exception as e:
            return e, False
    else:
        return 'API fail', False
