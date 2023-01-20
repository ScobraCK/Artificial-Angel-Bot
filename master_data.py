import json
import os
import requests
from typing import Iterable, Literal, Optional, List, Union

class MasterData():
    '''
    Class to help read the Master data.
    Use to search for the specific json objects or loading the json files
    '''
    def __init__(self, language: Optional[Literal['enUS', 'jaJP', 'koKR', 'zhTW']]='enUS') -> None:
        self.textdata = self.open_MB('TextResourceMB')  # is used most frequently

        # maybe make a data class inheriting dict
        # uses lazy loading for other jsons for now
        self.data = {}
        self.language = language
        
    def open_MB(self, dataMB: str):
        '''
        returns MB json(dict) object
        '''
        url = 'https://raw.githubusercontent.com/ScobraCK/MementoMori-data/main/Master'
        url = url + f'/{dataMB}'
        if not url.endswith('.json'):
            url = url + '.json'
        resp = requests.get(url)
        data = json.loads(resp.text)
        return data

    def load_all(self):
        '''
        load all main json files
        '''
        self.__load_MB('CharacterMB')
        self.__load_MB('EquipmentMB')
        self.__load_MB('CharacterProfileMB')
        self.__load_MB('ActiveSkillMB')
        self.__load_MB('PassiveSkillMB')
        self.__load_MB('EquipmentExclusiveSkillDescriptionMB')

    def get_textdata(self):
        return self.textdata

    def get_chardata(self):
        return self.__load_MB('CharacterMB')

    def get_MB_iter(self, dataMB: str) -> Iterable:
        '''
        For reading all data in a MB file
        Not meant to be used with large files
        '''
        return iter(self.__load_MB(dataMB))

    def __load_MB(self, dataMB: str):
        """
        same as open_MB but also loads MB json into the class

        to be used inside the class only
        """
        if dataMB not in self.data:
            self.data[dataMB] = self.open_MB(dataMB)
        return self.data[dataMB]

    def search_string_key(self, text_key: str, language: str = None)->str:
        '''
        Returns the text string for selected region

        language:
            English - enUS
            Japanese - jaJP
            Korean - koKR
            Taiwanese - zhTW
        '''
        if language is None:
            language = self.language

        obj = filter(lambda x:x["StringKey"]==text_key, self.textdata)
        try:
            text =  next(obj)[language]
            if text is None:
                return "null" # Key match but null data
            else:
                return text
        except StopIteration:  # No key match
            return None

    def search_id(self, id: int, data: dict) -> dict:
        obj = filter(lambda x:x["Id"]==id, data)
        try:
            return next(obj)
        except StopIteration:
            return None   

    def search_chars(self, *, \
        id: int=None, type: int=None, rarity: int=None, job: int=None) -> Iterable:
        '''
        Returns a iterator of characters matching search conditions
        '''
        if id:  # unique
            char = filter(lambda x:x["Id"]==id, self.__load_MB('CharacterMB'))
            return char

        if type:
            char = filter(lambda x:x["ElementType"]==type, self.__load_MB('CharacterMB'))
        if rarity:
            char = filter(lambda x:x["RarityFlags"]==rarity, char)
        if job:
            char = filter(lambda x:x["JobFlags"]==job, char)
        return char

    def search_uw(self, char_id)->Iterable:
        '''
        returns the an iterator of unique weapons (same weapon different lv)
        next() should give lv180

        returns None if char does not have uw
        '''
        profile = self.search_id(char_id, self.__load_MB('CharacterProfileMB'))
        if (composite_id := profile['EquipmentCompositeId']):
            equipment = filter(
                lambda x: x['CompositeId'] == composite_id,
                self.__load_MB('EquipmentMB'))
            return equipment
        else:
            return None

    def search_active_skill(self, skill_id):
        return self.search_id(skill_id, self.__load_MB('ActiveSkillMB'))

    def search_passive_skill(self, skill_id):
        return self.search_id(skill_id, self.__load_MB('PassiveSkillMB'))

    def search_uw_description(self, char_id):
        equipment = self.search_uw(char_id)
        if equipment:
            equipment = next(equipment)
            uw_id = equipment['EquipmentExclusiveSkillDescriptionId']
            return self.search_id(uw_id, self.__load_MB('EquipmentExclusiveSkillDescriptionMB'))
        else:
            return None    

    def search_item(self, id: int, type: str):
        '''
        searches ItemMB
        '''
        obj = filter(lambda x:x["ItemId"]==id and x['ItemType']==type,\
            self.__load_MB('ItemMB'))
        try:
            return next(obj)
        except StopIteration:
            return None

    def find_item(self, ItemId: int, ItemType: str, **_) -> dict:
        '''
        find item by ItemId and ItemType from multiple MB files

        **_ is to catch extra data if using **keyword arguments
        '''
        if ItemType == 14: # runes
            item = self.search_id(ItemId, self.__load_MB('SphereMB'))
        elif ItemType == 17: # containers
            item = self.search_id(ItemId, self.__load_MB('TreasureChestMB'))
        else: # In ItemMB
            item = self.search_item(ItemId, ItemType)

        if item is None:
            print(f'Item not found. Id: {ItemId} Type: {ItemType}')  # add later
        return item

    def search_missions(self, mission_list: Union[List, int]) -> Iterable:
        if isinstance(mission_list, int):
            mission_list = [mission_list]

        return filter(lambda x: x['Id'] in mission_list, self.__load_MB('MissionMB'))

        