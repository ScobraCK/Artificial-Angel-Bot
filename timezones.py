from enum import Enum
from datetime import datetime, timezone

class ServerUTC(Enum):
    NA = -7
    JP_KR = 9
    EU_GL = 1
    ASIA = 8


class DailyEvents():
    reset = 1680840000
    shop1 = 1680771600
    shop2 = 1680782400
    shop3 = 1680793200
    shop4 = 1680804000
    battle_league = 1680813000
    temple_open1 = 1680784200
    temple_close1 = 1680787800
    temple_open2 = 1680809400
    temple_close2 = 1680813000
    guild_strategy_start = 1680853500  # guild war
    guild_strategy_end = 1680813000
    guild_war_start = 1680813900
    guild_war_end = 1680816600
    grand_first_strategy = 1680808500
    grand_strategy_start = 1680853500
    grand_strategy_end = 1680813900
    grand_war_start = 1680817500
    grand_war_end = 1680820200


def convert_date_string(date: datetime):
    return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

def convert_date(date: str)->datetime:
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def convert_from_local(date: str, utc_diff: int)->int:
    '''returns unix timestamp from server time string'''
    return int(convert_date(date).replace(tzinfo=timezone.utc).timestamp()) - utc_diff*3600

def convert_from_jst(date: str)->int:
    '''returns unix timestamp from jst time string'''
    return int(convert_date(date).replace(tzinfo=timezone.utc).timestamp()) - 32400 # -9 hours

def local_to_unix(timestamp: datetime.timestamp, server: ServerUTC):
    '''converts local timestamps to unix'''
    return timestamp + server.value*3600

def unix_to_local(timestamp: datetime.timestamp, server: ServerUTC):
    '''converts unix timestamp to local time'''
    return timestamp - server.value*3600

def get_cur_time():
    '''Returns current time'''
    return convert_date_string(datetime.now(timezone('Asia/Seoul')))

if __name__ == "__main__":
    a = [1680821100, 1680780600, 1680781500, 1680784200, 1680776100, 1680821100, 1680781500,
         1680785100, 1680787800]
    
    for k in vars(DailyEvents):
        print(k)