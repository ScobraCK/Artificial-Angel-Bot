from master_data import MasterData
from typing import List, Iterator, Optional

from common import Language
import items

class Mission():
    '''
    Basic mission data class

    Parameters:
        name, open, reward_list
    '''
    def __init__(self, name:str, open: int, reward_list: List[items.Item]) -> None:
        self.name = name
        self.open = open # opening period
        self.reward_list = reward_list

    def __str__(self) -> str:
        text = f"**{self.name}**\n"
        if self.open:
            text += f"**Open**: Day {self.open}\n"
        text += "**Rewards**: "
        for reward in self.reward_list:
            text+=f'{reward} '
        return text

def get_Missions(
        mission_list: List[int], 
        master: MasterData, 
        lang: Optional[Language]='enUS') -> Iterator[Mission]:
    '''
    Returns an iterator of Missions(class) from the mission list
    '''
    mission_it = master.search_id_list(mission_list, 'MissionMB')
    
    try:
        while(mission := next(mission_it)):
            name = master.search_string_key(mission["NameKey"], language=lang) 
            open = mission["OpeningPeriod"]
            reward_list = []
            for item in mission["RewardList"]:  # "RewardList":[{"Item":{}, "RarityFlags":0}]
                reward_list.append(items.get_item(master, item['Item'], lang))
            yield Mission(name, open, reward_list)
    except StopIteration:
        pass

if __name__ == '__main__':
    ml = [723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735]
    master = MasterData()
    missions = get_Missions(ml, master)
    from pprint import pprint
    from helper import batched
    batch = batched(missions, 7)
    text = []
    for i, b in enumerate(batch):
        text.append('')
        for mission in b:
            text[i] += f"{mission}\n\n"

    print(text[0])