import sqlite3, requests, json
from enum import Enum
from dataclasses import dataclass
from logging import Logger, ERROR
import aiohttp, asyncio

from common import Tower, tower_map, Server
from models import GachaPickup
from timezones import check_time

@dataclass
class GuildData():
    world: int
    bp: int
    name: str

    def list_bp(self):
        return [self.bp, self.world, self.name]

class MememoriDB():
    def __init__(self) -> None:
        self.con = sqlite3.connect('/usr/src/app/data/memento.db')
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

        # self.cur.execute("""
        # CREATE TABLE IF NOT EXISTS groups (
        #     group_id int PRIMARY KEY,
        #     server int,
        #     start int,
        #     end int)
        # """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
                         id varchar(12) PRIMARY KEY,
                         server int,
                         world int,
                         name text,
                         auto_bp int,
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
        
        for tower_type in tower_map.values():
            self.cur.execute(f"""
                             CREATE TABLE IF NOT EXISTS {tower_type} (
                                 id varchar(12) PRIMARY KEY,
                                 tower_id int,
                                 timestamp datetime
                             )
                             """)

        # Gacha
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS gacha (
                         id int PRIMARY KEY,
                         start int,
                         end int,
                         select_list_type int,
                         char_id int
            )
        """)
    
    # INSERT
    def update_groups(self, group_data):
        for group in group_data:
            group_id = group['Id']
            server = group['TimeServerId']
            if not check_time(group['StartTime'], group['EndTime'], Server(server)):
                continue
            world_list = []
            for world_id in group['WorldIdList']:
                world = world_id % 1000
                world_list.append(world)
                # add to worlds
                self.cur.execute(
                    "INSERT OR REPLACE INTO worlds (world_id, group_id, world, server) VALUES (?, ?, ?, ?)",
                    (world_id, group_id, world, server))
            # # add to groups NOW UNUSED
            # self.cur.execute(
            #         "INSERT OR REPLACE INTO groups (group_id, server, start, end) VALUES (?, ?, ?, ?)",
            #         (group_id, server, world_list[0], world_list[-1]))
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
            "(id, server, world, name, auto_bp, rank, quest_id, tower_id, icon_id, guild_id, guild_join_time, guild_position, prev_legend_league_class, timestamp)"
            "VALUES (:id, :server, :world, :name, :bp, :rank, :quest_id, :tower_id, :icon_id, :guild_id, :guild_join_time, :guild_position, :prev_legend_league_class, :timestamp)",
            player_data)

    def update_players(self, server, world, data: dict, timestamp):
        player_info = data['player_info']
        bp_ranking = data['rankings']['bp']
        for player_data in player_info.values():
            self._insert_player(server, world, player_data, timestamp)
        for bp in bp_ranking:
            self.cur.execute(
                "INSERT OR REPLACE INTO players (id, name, bp)"
                "VALUES (:id, :name, :bp)"
                "ON CONFLICT(id) DO UPDATE SET bp=excluded.bp",
                bp)
            
        for tower_type in tower_map.values():
            for ele_tower in data['rankings'][tower_type]:
                self.cur.execute(
                    f"INSERT OR REPLACE INTO {tower_type} (id, tower_id, timestamp)"
                    "VALUES (?, ?, ?)",
                    (ele_tower['id'], ele_tower['tower_id'], timestamp))
        self.con.commit()

    def update_gacha(self, gacha_list: list[GachaPickup]):
        existing_ids = self._get_gacha_ids()
        new_gachas = filter(lambda gacha: gacha.id not in existing_ids, gacha_list)
        gacha_values = [(gacha.id, gacha.start, gacha.end, gacha.select_list_type, gacha.char_id) for gacha in new_gachas]
        if gacha_values:
            try:
                self.cur.executemany('''
                    INSERT INTO gacha (id, start, end, select_list_type, char_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', gacha_values)
                self.con.commit()
            except Exception as e:
                self.con.rollback()
                raise e
    
    # READ
    def get_group_list(self):
        '''
        return example
        grouped_data = [
            (1, 1, ['1', '2']),
            (1, 2, ['3']),
            (2, 1, ['4']),
            (2, 2, ['5', '6'])
        ]
        '''
        res = self.cur.execute(
            """SELECT server, group_id, GROUP_CONCAT(world) AS worlds
            FROM worlds
            GROUP BY server, group_id
            ORDER BY server, group_id;
            """)
        rows =  res.fetchall()
        grouped_data = []
        for row in rows:
            server, group_id, worlds_str = row
            worlds = worlds_str.split(',')  # Convert comma-separated string to list
            grouped_data.append((server, group_id, worlds))
            
        return grouped_data
    
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
    
    # def get_group_worlds(self, group_id):
    #     res = self.cur.execute(
    #         "SELECT start, end from groups WHERE group_id = (?)", (group_id, )
    #     )
    #     return res.fetchone()
    
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
        '''order can be bp, quest_id'''
        res = self.cur.execute(
            f"SELECT world, COALESCE(bp, 'Unknown'), COALESCE(quest_id, 'Unknown'), name FROM players WHERE server = (?) ORDER BY {order} DESC", (server, )
        )
        return res.fetchmany(200)        
    
    def get_all_player_ranking(self, order='bp'):
        '''
        order can be bp, quest_id
        None defaults to bp
        '''
        res = self.cur.execute(
            f"SELECT server, world, COALESCE(bp, 'Unknown'), COALESCE(quest_id, 'Unknown'), name FROM players ORDER BY {order} DESC"
        )
        return res.fetchmany(500)
    
    def get_server_tower_ranking(self, server, tower_type: Tower=Tower.Infinity, count=200):
        '''
        tower_type: Tower of Infinity is None
        '''
        if tower_type == Tower.Infinity:
            res = self.cur.execute(
                f"SELECT world, tower_id, name FROM players WHERE server = {server} ORDER BY tower_id DESC"
            )
        else:
            tower = tower_map.get(tower_type.value) 
            res = self.cur.execute(
                f"SELECT players.world, {tower}.tower_id, players.name "
                f"FROM {tower} "
                f"JOIN players ON {tower}.id = players.id "
                f"WHERE players.server = {server} "
                f"ORDER BY {tower}.tower_id DESC"
            )
            
        return res.fetchmany(200)
    
    def get_all_tower_ranking(self, tower_type: Tower=Tower.Infinity, count=200):
        '''
        tower_type: Tower of Infinity is None
        '''
        if tower_type == Tower.Infinity:
            res = self.cur.execute(
                "SELECT server, world, tower_id, name FROM players ORDER BY tower_id DESC"
            )
        else:
            tower = tower_map.get(tower_type.value) 
            res = self.cur.execute(
                f"SELECT players.server, players.world, {tower}.tower_id, players.name "
                f"FROM {tower} "
                f"JOIN players ON {tower}.id = players.id "
                f"ORDER BY {tower}.tower_id DESC"
            )
            
        return res.fetchmany(count)
    
    def get_last_update_guild(self):
        '''Get most recent timestamp from guild'''
        res = self.cur.execute('SELECT timestamp FROM guilds ORDER BY timestamp DESC LIMIT 1')
        return res.fetchone()[0]
    
    def get_last_update_player(self):
        '''Get most recent timestamp from player'''
        res = self.cur.execute('SELECT timestamp FROM players ORDER BY timestamp DESC LIMIT 1')
        return res.fetchone()[0]  

    def _get_gacha_ids(self) -> bool:
        '''get set of gacha ids to check existing'''
        self.cur.execute('SELECT id FROM gacha')
        return {item[0] for item in self.cur.fetchall()}

    def get_gacha_current(self, current: int, future=False):
        '''
        Get all gachas in given current timeframe.
        Will get future banners if future is True
        '''
        start = 4102444800 if future else current
        self.cur.execute('''
            SELECT id, start, end, select_list_type, char_id
            FROM gacha
            WHERE start <= ? AND end >= ?
            ORDER BY select_list_type
        ''', (start, current))

        return self.cur.fetchall()
    
    def get_gacha_char(self, char_id: int):
        '''
        Get all gachas for a character
        '''
        self.cur.execute('''
            SELECT id, start, end, select_list_type, char_id
            FROM gacha
            WHERE char_id = ?
            ORDER BY select_list_type
        ''', (char_id,))

        return self.cur.fetchall()

    def get_rerun_count(self, start: int, char_id: int) -> int:
        '''get rerun count of banners'''
        self.cur.execute('''
            SELECT COUNT(*)
            FROM gacha
            WHERE char_id = ?
            AND select_list_type IN (1, 3)  -- Only include fleeting and iosg
            AND start <= ?                  -- Include records that happened on or before the given start time
        ''', (char_id, start))

        return self.cur.fetchone()[0]

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
        try:
            data = json.loads(resp.content.decode('utf-8'))
            return data['data'], data['timestamp']
        except Exception as e:
            Logger.log(level=ERROR, msg=e)
            return None, None
    else:
        return None, None
    
def fetch_players():
    url = f"https://api.mentemori.icu/0/player_ranking/latest"
    resp = requests.get(url)
    if resp.status_code == 200:
        try:
            data = json.loads(resp.content.decode('utf-8'))
            return data['data'], data['timestamp']
        except Exception as e:
            Logger.log(level=ERROR, msg=e)
            return None, None
    else:
        return None, None
    
def fetch_worlddata():
    url = f"https://api.mentemori.icu/worlds"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.content.decode('utf-8'))
        return data['data']  # need error checks
    else:
        return None

# def fetch_group_list(server):
#     db = MememoriDB()
#     data = db.get_group_list(server)
#     db.close()
#     return data

def split_world_id(world_id):
    world_id = str(world_id)
    return int(world_id[0]), int(world_id[1:])

def update_guild_rankings(mdb: MememoriDB):
    guild_data, timestamp = fetch_guilds()
    if guild_data:
        try:
            for data in guild_data:
                server, world = split_world_id(data['world_id'])
                guilds = data['guild_info']
                mdb.update_guilds(server, world, guilds, timestamp)
            return "Updated guild rankings", timestamp
        except Exception as e:
            return e, None
    else:
        return 'API fail', None

def update_player_rankings(mdb: MememoriDB):
    player_data, timestamp = fetch_players()
    if player_data:
        try:
            for data in player_data:
                server, world = split_world_id(data['world_id'])
                mdb.update_players(server, world, data, timestamp)
            return "Updated player rankings", timestamp
        except Exception as e:
            return e, None
    else:
        return 'API fail', None

###### unused ######

async def async_fetch_guild(world_id):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.mentemori.icu/{world_id}/guild_ranking/latest"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                return None
            
            
async def async_update_guild_rankings(gdb: MememoriDB):
    world_data = fetch_worlddata()
    try:
        tasks = [async_fetch_guild(world['world_id']) for world in world_data if world['ranking']]
        guild_data = await asyncio.gather(*tasks)
        for resp in guild_data:
            if resp is not None:
                data = resp['data']
                timestamp = resp['timestamp']
                server, world = split_world_id(data['world_id'])
                guilds = data['guild_info']
                gdb.update_guilds(server, world, guilds, timestamp)
        return "Updated guild rankings", True

    except Exception as e:
        return e, False

async def async_fetch_player(world_id):
    url = f"https://api.mentemori.icu/{world_id}/player_ranking/latest"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                return None
            
async def async_update_player_rankings(gdb: MememoriDB):
    world_data = fetch_worlddata()
    try:
        tasks = [async_fetch_player(world['world_id']) for world in world_data if world['ranking']]
        player_data = await asyncio.gather(*tasks)
        for resp in player_data:
            if resp is not None:
                data = resp['data']
                timestamp = resp['timestamp']
                server, world = split_world_id(data['world_id'])
                gdb.update_players(server, world, data, timestamp)
        return "Updated player rankings", True
    except Exception as e:
        return e, False
