from datetime import datetime
from zoneinfo import ZoneInfo

import api.utils.enums as enums

timeserver2timezone = {
    1: ZoneInfo('Etc/GMT-9'),
    2: ZoneInfo('Etc/GMT-9'),
    3: ZoneInfo('Etc/GMT-8'),
    4: ZoneInfo('Etc/GMT+7'),
    5: ZoneInfo('Etc/GMT-1'),
    6: ZoneInfo('Etc/GMT-1'),
}

def convert_date(date: str)->datetime:
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def convert_from_jst(date_str: str) -> int:
    '''Returns unix timestamp from JST time string'''
    jst_date = convert_date(date_str)
    jst_date = jst_date.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
    return int(jst_date.timestamp())

def convert_from_local(date_str: str, server: enums.Server) -> int:
    '''Returns unix timestamp from server time string'''
    local_date = convert_date(date_str)
    tz = timeserver2timezone[server.value]
    local_date = local_date.replace(tzinfo=tz)
    return int(local_date.timestamp())

def is_active(start: str, end: str, server: enums.Server) -> bool:
    current = int(datetime.now(ZoneInfo("UTC")).timestamp())

    start_ts = convert_from_local(start, server)
    end_ts = convert_from_local(end, server)

    return start_ts <= current <= end_ts

def get_current() -> int:
    return int(datetime.now(ZoneInfo("UTC")).timestamp())