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

def human_format(num: int)->str:
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T'][magnitude])

def reverse_dict_search(dictionary, search_value):
    return [key for key, value in dictionary.items() if value == search_value][0]