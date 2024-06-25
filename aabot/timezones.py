from datetime import datetime, timezone, time
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

class DailyEvents:
    reset = time(4, 0)
    shop1 = time(9, 0)
    shop2 = time(12, 0)
    shop3 = time(15, 0)
    shop4 = time(18, 0)
    pvp_reset = time(20, 30)
    legend_league_start = time(21, 0)
    temple_open1 = time(12, 30)
    temple_close1 = time(13, 30)
    temple_open2 = time(19, 30)
    temple_close2 = time(20, 30)
    guild_strategy_start = time(7, 45)
    guild_strategy_end = time(20, 30)
    guild_war_start = time(20, 45)
    guild_war_end = time(21, 30)

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

def time_to_local(time: time, server: Server) -> int:
    '''Converts daily times to local timestamp'''
    current_date = datetime.now(timeserver2timezone[server.value]).date()
    converte_date = datetime.combine(current_date, time, tzinfo=timeserver2timezone[server.value])
    return int(converte_date.timestamp())

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
    timestamp = 1680840000  # Example Unix timestamp
    server = Server.Japan   # Example server

    times = [time(4, 0), time(5, 0), time(6, 0)]
    current_date = datetime.now(timeserver2timezone[server.value]).date()