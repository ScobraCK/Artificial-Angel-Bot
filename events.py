'''
Scripts for getting event data from
NewCharacterMissionMB
LimitedEventMB
LimitedLoginBonusMB
LimitedMissionMB
BountyQuestEventMB

LimitedLoginBonusRewardMB
'''

from datetime import datetime, timezone
from typing import List, Literal

from master_data import MasterData
from emoji import emoji_list
from character import get_name
from items import get_item_name
from common import Server

class MM_Event():
    '''
    Basic event data
    name, desc, start, end, utc_diff
    '''
    def __init__(
        self, 
        name: str,
        start: int, end: int, server: Server) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.server = server
        self.description=None
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


class NewCharacter(MM_Event):
    '''
    Has force_start, mission_list
    '''
    def __init__(
        self, name: str,
        start: int, end: int, force_start: int, server: Server, 
        mission_list: List, character: str) -> None:

        super().__init__(name, start, end, server)
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
        start: int, end: int, server: Server,
        mission_list: List) -> None:

        super().__init__(name, start, end, server)
        self.has_mission = True
        self.mission_list = mission_list
        self.type_indication = emoji_list.get('blue dia')

class LimitedLogin(MM_Event):
    '''Has Reward List'''
    pass  #todo

# speculative bounty types for "TargetQuestTypeList" (unused)
bounty_type = {
    0: 'Normal',
    1: 'Team',
    2: 'Guerrilla'
}

class BountyQuest(MM_Event):
    '''
    Has TargetItemList[str], multiplier
    '''

    def __init__(self, name: str, start: int, end: int, server: Server, 
                description: str, targets: List[str], multiplier: int) -> None:
        super().__init__(name, start, end, server)
        self.description = description
        self.targets = targets
        self.multiplier = multiplier
        self.type_indication = emoji_list.get('black dia')

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

def has_ended(end: int):
    now = datetime.utcnow().timestamp()
    return end < now


def get_timestamp(
    item, time_str: Literal['StartTime', 'EndTime', 'ForceStartTime'], server: Server) -> int:
    '''
    gets timestamp for time_str
    '''
    time = item.get(time_str)
    utc_diff = server.value
    if time:
        timestamp = convert_timestamp_local(time, utc_diff)
    else:  # add fixJST
        time_str += 'FixJST'
        time = item.get(time_str)
        timestamp = convert_timestamp_jst(time)

    return timestamp

def get_NewCharacter(
    master: MasterData, lang = 'enUS', server:Server=Server.NA ,get_past: bool=False)->List[NewCharacter]:
    '''
    Returns a list of NewCharacterMission events
    '''
    event_list = []
    data_it = master.get_MB_iter('NewCharacterMissionMB')
    for item in data_it:
        end = get_timestamp(item, 'EndTime', server)
        if has_ended(end) and not get_past: # skip passed events
            continue
        start = get_timestamp(item, 'StartTime', server)
        name = master.search_string_key(item.get('TitleTextKey'), language=lang)
        force_start = get_timestamp(item, "ForceStartTime", server)
        character = get_name(item.get("CharacterImageId"), master, lang)  # is character id

        event = NewCharacter(
            name, start, end, force_start, server, item.get("TargetMissionIdList"), character)
        event_list.append(event)
    return event_list

def get_LimitedMission(
    master: MasterData, lang = 'enUS', server:Server=Server.NA, get_past:bool=False)->List[LimitedMission]:
    '''
    Returns a list of LimitedMission events
    '''
    event_list = []
    data_it = master.get_MB_iter('LimitedMissionMB')
    for item in data_it:
        end = get_timestamp(item, 'EndTime', server)
        if has_ended(end) and not get_past: # skip passed events
            continue
        start = get_timestamp(item, 'StartTime', server)
        name = master.search_string_key(item.get('TitleTextKey'), language=lang)
        event = LimitedMission(name, start, end, server, item.get("TargetMissionIdList"))
        event_list.append(event)
    return event_list

def get_BountyQuest(
    master: MasterData, lang = 'enUS', server:Server=Server.NA, get_past:bool=False)->List[BountyQuest]:
    event_list = []
    data_it = master.get_MB_iter('BountyQuestEventMB')
    for item in data_it:
        end = get_timestamp(item, 'EndTime', server)
        if has_ended(end) and not get_past: # skip passed events
            continue
        start = get_timestamp(item, 'StartTime', server)
        name = master.search_string_key(item.get('EventNameKey'), language=lang)
        description = master.search_string_key(item.get('EventDescriptionKey'), language=lang)
        mul = item.get('MultipleNumber')

        target_list = item.get('TargetItemList') # namespace is overlapping with item
        targets = []
        for target in target_list:
            target_item = master.find_item(**target)
            item_name = get_item_name(master, target_item, lang)
            targets.append(item_name)
        event = BountyQuest(name, start, end, server, description, targets, mul)
        event_list.append(event)
    return event_list


# add more events later
def get_all_events(
    master: MasterData, lang = 'enUS', server:Server=Server.NA, get_past:bool=False)->List[MM_Event]:
    '''
    Returns a list of all events
    '''
    event_list = []
    event_list += get_LimitedMission(master, lang, server,get_past)
    event_list += get_NewCharacter(master, lang, server, get_past)
    event_list += get_BountyQuest(master, lang, server, get_past)
    return event_list


if __name__ == "__main__":
    from pprint import pprint
    events = get_all_events(MasterData(), server=Server.NA)
    for e in events:
        pprint(e.__dict__)