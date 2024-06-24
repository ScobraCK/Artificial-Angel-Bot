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
from typing import List, Literal, Optional

from master_data import MasterData
from emoji import emoji_list
from character import get_name
from items import get_item_name
from common import Server, Language
from timezones import convert_from_local, convert_from_jst, get_cur_timestamp_UTC

class MM_Event():
    '''
    Parent class with basic event data

    Parameters:
        name, desc, start, end, server

    Additional attributes:
        description, type_indication, has_mission(bool), has_force_start(bool)
        *type_indication is an emoji string
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
        now = get_cur_timestamp_UTC()
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

def has_ended(end: int):
    now = get_cur_timestamp_UTC()
    return end < now

def get_timestamp(
    data, 
    time_str: Literal['StartTime', 'EndTime', 'ForceStartTime'], 
    server: Server) -> int:
    '''
    gets timestamp for time_str('StartTime', 'EndTime', 'ForceStartTime')
    '''
    time = data.get(time_str)
    if time:
        timestamp = convert_from_local(time, server)
    else:  # add fixJST
        time_str += 'FixJST'
        time = data.get(time_str)
        timestamp = convert_from_jst(time)

    return timestamp

def get_NewCharacter(
    master: MasterData, 
    lang: Optional[Language]='enUS', 
    server:Server=Server.America,
    past: bool=False)->List[NewCharacter]:
    '''
    Returns a list of NewCharacterMission events
    '''
    event_list = []
    data_it = master.get_MB_iter('NewCharacterMissionMB')
    for data in data_it:
        end = get_timestamp(data, 'EndTime', server)
        if has_ended(end) and not past: # skip passed events
            continue
        start = get_timestamp(data, 'StartTime', server)
        name = master.search_string_key(data.get('TitleTextKey'), language=lang)
        force_start = get_timestamp(data, "ForceStartTime", server)
        character = get_name(data.get("CharacterImageId"), master, lang)  # is character id

        event = NewCharacter(
            name, start, end, force_start, server, data.get("TargetMissionIdList"), character)
        event_list.append(event)
    return event_list

def get_LimitedMission(
    master: MasterData, 
    lang: Optional[Language]='enUS', 
    server:Server=Server.America, 
    past:bool=False)->List[LimitedMission]:
    '''
    Returns a list of LimitedMission events
    '''
    event_list = []
    data_it = master.get_MB_iter('LimitedMissionMB')
    for data in data_it:
        end = get_timestamp(data, 'EndTime', server)
        if has_ended(end) and not past: # skip passed events
            continue
        start = get_timestamp(data, 'StartTime', server)
        name = master.search_string_key(data.get('TitleTextKey'), language=lang)
        event = LimitedMission(name, start, end, server, data.get("TargetMissionIdList"))
        event_list.append(event)
    return event_list

def get_BountyQuest(
    master: MasterData, 
    lang: Optional[Language]='enUS', 
    server:Server=Server.America, 
    get_past:bool=False)->List[BountyQuest]:
    event_list = []
    data_it = master.get_MB_iter('BountyQuestEventMB')
    for data in data_it:
        end = get_timestamp(data, 'EndTime', server)
        if has_ended(end) and not get_past: # skip passed events
            continue
        start = get_timestamp(data, 'StartTime', server)
        name = master.search_string_key(data.get('EventNameKey'), language=lang)
        description = master.search_string_key(data.get('EventDescriptionKey'), language=lang)
        mul = data.get('MultipleNumber')

        target_list = data.get('TargetItemList')  # List containing target items for event
        targets = []
        for target in target_list:
            target_item = master.find_item(**target)
            item_name = get_item_name(master, target_item, lang)
            targets.append(item_name)
        event = BountyQuest(name, start, end, server, description, targets, mul)
        event_list.append(event)
    return event_list


def get_all_events(
    master: MasterData, 
    lang: Optional[Language]='enUS', 
    server:Server=Server.America, 
    past:bool=False)->List[MM_Event]:
    '''
    Returns a list of all events
    '''
    event_list = []
    event_list += get_LimitedMission(master, lang, server,past)
    event_list += get_NewCharacter(master, lang, server, past)
    event_list += get_BountyQuest(master, lang, server, past)
    return event_list

if __name__ == "__main__":
    from pprint import pprint
    events = get_all_events(MasterData(), server=Server.America)
    for e in events:
        pprint(e.__dict__)