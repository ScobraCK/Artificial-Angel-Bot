from typing import List, Optional
from master_data import MasterData
from common import Language

class Item():
    '''
    Item data. Consists of name and count.
    '''
    def __init__(self, name, count, id, type) -> None:
        self.name = name
        self.count = count
        self.id = id
        self.type = type

    def __str__(self) -> str:
        return f"{self.count:,}x {self.name}"
    
    def __add__(self, other):
        if isinstance(other, Item) and self.name == other.name:
            return Item(self.name, self.count + other.count, self.id, self.type)
        else:
            raise TypeError
        
    def __eq__(self, other) -> bool:
        if isinstance(other, Item):
            return True if (self.id == other.id and self.type == other.type) else False 
        else:
            raise TypeError

def get_item_name(master: MasterData, item: dict|str, lang: Optional[Language]='enUS')->str:
    '''
    gets item name from it's json data
    '''
    if item is None:  # need to add the item in
        return '[null(not found)]'
    if isinstance(item, str):
        return item
    name = master.search_string_key(item['NameKey'], language=lang)

    if ('SphereType') in item:  # runes
        lv = str(item["Lv"])
        name = name + ' Lv.' + lv

    return name

def get_item(master: MasterData, item_info: dict, lang: Optional[Language]='enUS')->Item:
    '''
    Input Item{ItemCount, ItemId, ItemType}
    
    Output Item class
    '''
    if item_info['ItemType'] == 9: # EquipmentSetMaterial
        return None
    item = master.find_item(**item_info)
    item_name = get_item_name(master, item, lang)

    return Item(item_name, item_info['ItemCount'], item_info['ItemId'], item_info['ItemType'])

def get_item_list(master: MasterData, raw_item_list: List, lang: Optional[Language]='enUS')->List[Item]:
    item_list = []
    if raw_item_list:
        for item_data in raw_item_list:
            if item := get_item(master, item_data, lang):
                item_list.append(item)
    return item_list