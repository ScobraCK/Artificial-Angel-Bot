from enum import Enum
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from common import Server

timeserver2timezone = {
    1: ZoneInfo('Etc/GMT-9'),
    2: ZoneInfo('Etc/GMT-9'),
    3: ZoneInfo('Etc/GMT-8'),
    4: ZoneInfo('Etc/GMT+7'),
    5: ZoneInfo('Etc/GMT-1'),
    6: ZoneInfo('Etc/GMT-1'),
}

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

def convert_from_local(date_str: str, server: Server) -> int:
    '''Returns unix timestamp from server time string'''
    local_date = convert_date(date_str)
    tz = timeserver2timezone[server.value]
    local_date = local_date.replace(tzinfo=tz)
    return int(local_date.timestamp())

def convert_from_jst(date_str: str) -> int:
    '''Returns unix timestamp from JST time string'''
    jst_date = convert_date(date_str)
    jst_date = jst_date.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
    return int(jst_date.timestamp())

def local_to_unix(timestamp: int, server: Server) -> int:
    '''Converts local timestamps to unix'''
    tz = timeserver2timezone[server.value]
    local_date = datetime.fromtimestamp(timestamp, tz)
    return int(local_date.timestamp())

def unix_to_local(timestamp: int, server: Server) -> str:
    '''Converts unix timestamp to local time'''
    tz = timeserver2timezone[server.value]
    local_date = datetime.fromtimestamp(timestamp, tz)
    return convert_date_string(local_date)

def get_cur_timestr_KR() -> str:
    '''Returns current time string in Asia/Seoul timezone'''
    return convert_date_string(datetime.now(ZoneInfo('Asia/Seoul')))

def get_cur_timestamp_UTC() -> int:
    '''Returns the current time as a Unix timestamp (UTC)'''
    return int(datetime.now(timezone.utc).timestamp())

def check_time(start: str, end: str, server: Server) -> bool:
    '''Checks if current time is within the start and end time for the given server'''
    tz = timeserver2timezone[server.value]
    start_timestamp = convert_date(start).replace(tzinfo=tz)
    end_timestamp = convert_date(end).replace(tzinfo=tz)
    cur = datetime.now(tz=tz)
    return start_timestamp <= cur <= end_timestamp
    
if __name__ == "__main__":
    print(check_time('2024-06-20 09:00:00', '2024-06-24 12:00:00', Server.America))
