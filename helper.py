from datetime import datetime, timezone
from itertools import islice

def convert_date_string(date: datetime):
    return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

def convert_date(date: str)->datetime:
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def convert_timestamp_local(date: str, utc_diff: int)->int:
    '''returns unix timestamp from server time string'''
    return int(convert_date(date).replace(tzinfo=timezone.utc).timestamp()) - utc_diff*3600

def convert_timestamp_jst(date: str)->int:
    '''returns unix timestamp from jst time string'''
    return int(convert_date(date).replace(tzinfo=timezone.utc).timestamp()) - 32400 # -9 hours

def batched(iterable, n):
    "Batch data into lists of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            return
        yield batch