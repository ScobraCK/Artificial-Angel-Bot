from master_data import MasterData

class Reward():
    '''
    Reward data
    '''
    def __init__(self, name, count) -> None:
        self.name = name
        self.count = count

    def __str__(self) -> str:
        return f"{self.count}x {self.name}"

def get_item_name(master: MasterData, item: dict, lang='enUS')->str:
    '''
    gets item name from it's json data
    '''
    if item is None:
        return '[null(not found)]'
    name = master.search_string_key(item['NameKey'], language=lang)

    if ('SphereType') in item:  # runes
        lv = str(item["Lv"])
        name = name + ' Lv.' + lv

    return name

def get_reward(reward: dict, master: MasterData, lang) ->dict:
    '''
    Input Reward{ItemCount, ItemId, ItemType}
    
    Output Reward{name, count}
    '''
    item = master.find_item(**reward)
    item_name = get_item_name(master, item, lang)

    return Reward(item_name, reward['ItemCount'])