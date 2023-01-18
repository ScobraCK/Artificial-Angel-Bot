'''
Scripts for getting event data from
NewCharacterMissionMB
LimitedEventMB
LimitedLoginBonusMB
LimitedMissionMB
BountyQuestEventMB

LimitedLoginBonusRewardMB
'''

from datetime import datetime
from typing import List

from master_data import MasterData
from emoji import emoji_list
from character import get_name

class MM_Event():
    '''
    Basic event data
    name, desc, start, end, utc_diff
    '''
    def __init__(
        self, 
        name: str,
        start: int, end: int) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.type_indication = None # diamond Emoji for type
        # flags
        self.has_mission = False
        self.has_force_start = False
    
    def state(self) -> int:
        '''
        Returns event state.

        -1: Past Event
        0: Ongoing Event
        1: Future Event
        '''
        now = datetime.utcnow().timestamp()
        if self.end < now:
            return -1
        elif now < self.start:
            return 1
        else:
            return 0
        

    def has_ended(self) -> bool:
        now = datetime.utcnow().timestamp()
        return self.end < now

class NewCharacterEvent(MM_Event):
    '''
    Has force_start, mission_list
    '''
    def __init__(
        self, name: str,
        start: int, end: int,
        force_start: int, mission_list: List, character: str) -> None:

        super().__init__(name, start, end)
        self.has_force_start = True
        self.has_mission = True
        self.force_start = force_start
        self.mission_list = mission_list
        self.character = character
        self.type_indication = emoji_list.get('orange dia')

class LimitedMission(MM_Event):
    '''
    Has mission_list
    '''
    def __init__(
        self, name: str,
        start: int, end: int,
        mission_list: List) -> None:

        super().__init__(name, start, end)
        self.has_mission = True
        self.mission_list = mission_list
        self.type_indication = emoji_list.get('blue dia')

def get_date_string(date: datetime):
    return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

def get_date(date: str)->datetime:
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def get_timestamp_jst(date: str)->int:
    '''returns unix timestamp from jst time string'''
    return int(datetime.strptime(date, '%Y-%m-%d %H:%M:%S').timestamp() - 32400) # -9 hours

def has_ended(end: int):
    now = datetime.utcnow().timestamp()
    return end < now


# BOI changing json keys smh
def get_start(mission_data):
    '''
    get "StartTime" or if None, "StartTimeFixJST"
    '''
    start = mission_data.get('StartTime')
    if start is None:
        start = mission_data.get('StartTimeFixJST')
    return start

def get_end(mission_data):
    '''
    get "EndTime" or if None, "EndTimeFixJST"
    '''
    end = mission_data.get('EndTime')
    if end is None:
        end = mission_data.get('EndTimeFixJST')
    return end

def get_NewCharacterMission(
    master: MasterData, lang = 'enUS', get_past: bool=False)->List:
    '''
    Returns a list of NewCharacterMission events
    '''
    event_list = []
    data_it = master.get_MB_iter('NewCharacterMissionMB')
    for item in data_it:
        end = get_timestamp_jst(get_end(item))
        if has_ended(end) and not get_past: # skip passed events
            continue
        start = get_timestamp_jst(get_start(item))
        name = master.search_string_key(item.get('TitleTextKey'), language=lang)
        force_start = get_timestamp_jst(item.get("ForceStartTime"))
        character = get_name(item.get("CharacterImageId"), master, lang)  # is character id

        event = NewCharacterEvent(
            name, start, end, force_start, item.get("TargetMissionIdList"), character)
        event_list.append(event)
    return event_list

def get_LimitedMission(
    master: MasterData, lang = 'enUS', get_past:bool=False)->List:
    '''
    Returns a list of LimitedMission events
    '''
    event_list = []
    data_it = master.get_MB_iter('LimitedMissionMB')
    for item in data_it:
        end = get_timestamp_jst(get_end(item))
        if has_ended(end) and not get_past: # skip passed events
            continue
        start = get_timestamp_jst(get_start(item))
        name = master.search_string_key(item.get('TitleTextKey'), language=lang)
        event = LimitedMission(name, start, end, item.get("TargetMissionIdList"))
        event_list.append(event)
    return event_list

# add more events later
def get_all_events(
    master: MasterData, lang = 'enUS', get_past:bool=False)->List[MM_Event]:
    '''
    Returns a list of all events
    '''
    event_list = []
    event_list += get_LimitedMission(master, lang, get_past)
    event_list += get_NewCharacterMission(master, lang, get_past)

    return event_list


if __name__ == "__main__":
    from pprint import pprint
    # events = get_all_events(MasterData(), get_past=True)
    # for e in events:
    #     pprint(e.__dict__)
    text = 'ケルベロス登場記念ミッション'
    print(text.split())