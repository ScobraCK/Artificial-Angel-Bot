'''
Scripts for getting event data from
NewCharacterMissionMB
LimitedEventMB
LimitedLoginBonusMB
LimitedMissionMB
BountyQuestEventMB

LimitedLoginBonusRewardMB
'''

from datetime import datetime, timedelta
from typing import List

from master_data import MasterData
import common

class MM_Event():
    '''
    Basic event data
    name, desc, start, end, utc_diff
    '''
    def __init__(
        self, 
        name: str,
        start: str, end: str, utc_diff: int) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.utc_diff = utc_diff
        # flags
        self.has_mission = False
        self.has_force_start = False
    
    def is_ongoing(self) -> bool:
        now = datetime.now() + timedelta(hours=self.utc_diff)
        return get_date(self.start) <= now <= get_date(self.end)

class NewCharacterEvent(MM_Event):
    '''
    Has force_start, mission_list
    '''
    def __init__(
        self, name: str,
        start: str, end: str, utc_diff: int,
        force_start: str, mission_list: List) -> None:

        super().__init__(name, start, end, utc_diff)
        self.has_force_start = True
        self.has_mission = True
        self.force_start = force_start
        self.mission_list = mission_list

class LimitedMission(MM_Event):
    '''
    Has mission_list
    '''
    def __init__(
        self, name: str,
        start: str, end: str, utc_diff: int,
        mission_list: List) -> None:

        super().__init__(name, start, end, utc_diff)
        self.has_mission = True
        self.mission_list = mission_list

def get_date_string(date: datetime):
    return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

def get_date(date: str)->datetime:
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def get_NewCharacterMission(
    master: MasterData, lang = 'enUS', timezone: common.Timezone=common.Timezone.NA, all=False)->List:
    '''
    Returns a list of NewCharacterMission events

    Returns all the events even old ones
    '''
    utc_diff = timezone.value
    event_list = []
    data_it = master.get_MB_iter('NewCharacterMissionMB')
    for item in data_it:
        name = master.search_string_key(item.get('TitleTextKey'), language=lang)
        start = item.get("StartTime")
        end = item.get("EndTime")
        force_start = item.get("ForceStartTime")
        event = NewCharacterEvent(name, start, end, utc_diff, force_start, item.get("TargetMissionIdList"))
        if all or event.is_ongoing():
            event_list.append(event)
    return event_list

def get_LimitedMission(
    master: MasterData, lang = 'enUS', timezone: common.Timezone=common.Timezone.NA, all=False)->List:
    '''
    Returns a list of LimitedMission events

    Returns all the events even old ones
    '''
    utc_diff = timezone.value
    event_list = []
    data_it = master.get_MB_iter('LimitedMissionMB')
    for item in data_it:
        name = master.search_string_key(item.get('TitleTextKey'), language=lang)
        start = item.get("StartTime")
        end = item.get("EndTime")
        event = LimitedMission(name, start, end, utc_diff, item.get("TargetMissionIdList"))
        if all or event.is_ongoing():
            event_list.append(event)
    return event_list

# add more events later
def get_all_events(
    master: MasterData, lang = 'enUS', timezone: common.Timezone=common.Timezone.NA, all=False)->List[MM_Event]:
    '''
    Returns a list of all events
    '''
    event_list = []
    event_list += get_LimitedMission(master,  lang, timezone, all)
    event_list += get_NewCharacterMission(master, lang, timezone, all)

    return event_list


if __name__ == "__main__":
    from pprint import pprint
    events = get_all_events(MasterData(), all=True)
    for e in events:
        pprint(e.__dict__)