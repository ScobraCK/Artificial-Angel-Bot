from datetime import datetime, time
from zoneinfo import ZoneInfo

from common.enums import Server

timeserver2timezone = {
    Server.Japan: ZoneInfo('Etc/GMT-9'),
    Server.Korea: ZoneInfo('Etc/GMT-9'),
    Server.Asia: ZoneInfo('Etc/GMT-8'),
    Server.America: ZoneInfo('Etc/GMT+7'),
    Server.Europe: ZoneInfo('Etc/GMT-1'),
    Server.Global: ZoneInfo('Etc/GMT-1'),
}

# default start and end times for events without specified times
START_TIME = "2020-01-01 00:00:00"
END_TIME = '2100-12-31 23:59:59'

def convert_date(date: str) -> datetime:
    '''Converts date string to datetime object'''
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def convert_date_string(date: datetime) -> str:
    '''Converts datetime object to date string'''
    return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

def convert_from_jst(date_str: str) -> int:
    '''Returns unix timestamp from JST time string'''
    jst_date = convert_date(date_str)
    jst_date = jst_date.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
    return int(jst_date.timestamp())

def convert_from_local(date_str: str, server: Server) -> int:
    '''Returns unix timestamp from server time string'''
    local_date = convert_date(date_str)
    tz = timeserver2timezone[server]
    local_date = local_date.replace(tzinfo=tz)
    return int(local_date.timestamp())

def get_current() -> int:
    '''Returns current timestamp in UTC'''
    return int(datetime.now(ZoneInfo("UTC")).timestamp())

def check_active(start: str, end: str, server: Server, include_future=False) -> bool:
    '''Checks if the current time is within the active period defined by start and end strings'''
    current = get_current()

    start_ts = convert_from_local(start, server)
    end_ts = convert_from_local(end, server)

    if include_future:
        return current <= end_ts
    else:
        return start_ts <= current <= end_ts

# Timestamps for significant daily events in the game
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

def time_to_local(time: time, server: Server) -> int:
    '''Converts times objects from DailyEvents to local timestamp'''
    current_date = datetime.now(timeserver2timezone[server]).date()
    convert_date = datetime.combine(current_date, time, tzinfo=timeserver2timezone[server])
    return int(convert_date.timestamp())