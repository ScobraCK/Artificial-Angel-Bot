from master_data import MasterData
from typing import List, Iterator
from itertools import islice

class Reward():
    '''
    Reward data
    '''
    def __init__(self, name, count) -> None:
        self.name = name
        self.count = count

    def __str__(self) -> str:
        return f"{self.count}x {self.name}"

class Mission():
    '''
    Basic mission data
    '''
    def __init__(self, name:str, open: int, reward_list: List[Reward]) -> None:
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


def get_reward(reward: dict, master: MasterData, lang) ->dict:
    '''
    Input Reward{
        ItemCount, ItemId, ItemType
    }
    
    Output Reward{
        name, count
    }
    '''
    item = master.find_item(reward['ItemId'], reward['ItemType'])
    if item is None:
        return
    item_name = master.search_string_key(item['NameKey'], language=lang)

    if reward['ItemType'] == 14:  # runes
        lv = str(item["Lv"])
        item_name = item_name + ' Lv.' + lv
    
    return Reward(item_name, reward['ItemCount'])

def get_Missions(mission_list, master: MasterData, lang = 'enUS') -> Iterator[Mission]:
    mission_it = master.search_missions(mission_list)
    
    try:
        while(mission := next(mission_it)):
            name = master.search_string_key(mission["NameKey"], language=lang) 
            open = mission["OpeningPeriod"]
            reward_list = []
            for item in mission["RewardList"]:  # "RewardList":[{"Item":{}, "RarityFlags":0}]
                reward_list.append(get_reward(item['Item'], master, lang))
            yield Mission(name, open, reward_list)
    except StopIteration:
        pass

def batched(iterable, n):
    "Batch data into lists of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            return
        yield batch

if __name__ == '__main__':
    ml = [723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735]
    master = MasterData()
    missions = get_Missions(ml, master)
    from pprint import pprint
    batch = batched(missions, 7)
    text = []
    for i, b in enumerate(batch):
        text.append('')
        for mission in b:
            text[i] += f"{mission}\n\n"

    print(text[0])