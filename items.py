from typing import List, Optional
from master_data import MasterData
from common import Language

class Reward():
    '''
    Reward data. Consists of name and count.
    '''
    def __init__(self, name, count) -> None:
        self.name = name
        self.count = count

    def __str__(self) -> str:
        return f"{self.count:,}x {self.name}"

def get_item_name(master: MasterData, item: dict, lang: Optional[Language]='enUS')->str:
    '''
    gets item name from it's json data
    '''
    if item is None:  # need to add the item in
        return '[null(not found)]'
    name = master.search_string_key(item['NameKey'], language=lang)

    if ('SphereType') in item:  # runes
        lv = str(item["Lv"])
        name = name + ' Lv.' + lv

    return name

def get_reward(master: MasterData, reward: dict, lang: Optional[Language]='enUS')->Reward:
    '''
    Input Reward{ItemCount, ItemId, ItemType}
    
    Output Reward class
    '''
    item = master.find_item(**reward)
    item_name = get_item_name(master, item, lang)

    return Reward(item_name, reward['ItemCount'])

def get_reward_list(master: MasterData, reward_list: List, lang: Optional[Language]='enUS')->List[Reward]:
    rewards = []
    if reward_list:
        for item in reward_list:
            rewards.append(get_reward(master, item, lang))
    return rewards