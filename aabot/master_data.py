import json
import requests
from typing import Iterable, Iterator, Literal, Optional, List, Union
from common import Language

class MasterData():
    '''
    Class to help read the Master data.
    Main API for reading the master data or searching for specific files
    '''
    def __init__(self, language: Optional[Literal['enUS', 'jaJP', 'koKR', 'zhTW']]='enUS') -> None:
        # uses lazy loading for other jsons
        self.data = {}
        self.language = language
        
    def open_MB(self, dataMB: str):
        '''
        returns the MB json(dict) directly

        Does not save the data in the class, refer to __load_MB.
        '''
        url = 'https://raw.githubusercontent.com/ScobraCK/MementoMori-data/main/Master/'
        url = url + f'{dataMB}'
        if not url.endswith('.json'):
            url = url + '.json'
        resp = requests.get(url)
        data = json.loads(resp.text)
        return data

        # path = "C:/Projects/MementoMori-data/Master/" + dataMB +'.json'
        # with open(path, 'r', encoding='utf-8') as f:
        #     return json.load(f)

    def load_all(self):
        '''
        loads all main json files into the class
        '''
        self.__load_MB('TextResourceEnUsMB')
        self.__load_MB('CharacterMB')
        self.__load_MB('EquipmentMB')
        self.__load_MB('CharacterProfileMB')
        self.__load_MB('ActiveSkillMB')
        self.__load_MB('PassiveSkillMB')
        self.__load_MB('EquipmentExclusiveSkillDescriptionMB')
        self.__load_MB('ItemMB')
        self.__load_MB('MissionMB')
        self.__load_MB('BossBattleEnemyMB')
        self.__load_MB('TowerBattleEnemyMB')
        self.__load_MB('TowerBattleQuestMB')
        self.__load_MB('EquipmentEvolutionMB')
        self.__load_MB('EquipmentCompositeMB')
        self.__load_MB('EquipmentReinforcementMaterialMB')
        self.__load_MB('EquipmentReinforcementParameterMB')
        self.__load_MB('EquipmentExclusiveEffectMB')
        self.__load_MB('CharacterDetailVoiceMB')
        self.__load_MB('CharacterStoryMB')

    def reload_all(self):
        self.textdata = self.open_MB('TextResourceMB')
        self.data.clear()
        self.load_all()

    def get_textdata(self):
        '''
        returns a copy of TextResourceMB
        '''
        return self.textdata

    def get_chardata(self):
        '''
        returns a copy of CharacterMB
        '''
        return self.__load_MB('CharacterMB')

    def get_MB_iter(self, dataMB: str) -> Iterable:
        '''
        For reading all data in a MB file
        Not meant to be used with large files
        '''
        return iter(self.__load_MB(dataMB))
    
    def get_MB_data(self, dataMB: str):
        '''cause not having this was inconvenient'''
        return self.__load_MB(dataMB)

    def __load_MB(self, dataMB: str):
        """
        same as open_MB but also loads MB json into the class

        to be used inside the class
        """
        if dataMB not in self.data:
            self.data[dataMB] = self.open_MB(dataMB)
        return self.data[dataMB]

    def search_string_key(self, text_key: str, language: Union[str, Language]=None)->str:
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
        elif isinstance(language, Language):
            language = language.value

        if language == 'enUS':  # smh hardcoded language option fail
            language = 'EnUs'

        obj = filter(lambda x:x["StringKey"]==text_key, self.__load_MB(f'TextResource{language}MB'))
        try:
            text =  next(obj)['Text']
            if text is None:
                return "null" # Key match but null data
            else:
                return text
        except StopIteration:  # No key match
            return None

    def search_id(self, id: int, dataMB: str) -> dict:
        '''
        Searches a specific master file for a matching Id
        '''
        obj = filter(lambda x:x["Id"]==id, self.__load_MB(dataMB))
        try:
            return next(obj)
        except StopIteration:
            return None   

    def search_chars(self, *, \
        id: int=None, type: int=None, rarity: int=None, job: int=None) -> Iterable:
        '''
        Returns a iterator of characters matching search conditions

        may be subject to change after implementing other search features
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
        profile = self.search_id(char_id, 'CharacterProfileMB')
        if profile is None:
            return None  # temp solution for undefined data
        if (composite_id := profile.get('EquipmentCompositeId')):
            equipment = filter(
                lambda x: x['CompositeId'] == composite_id,
                self.__load_MB('EquipmentMB'))
            return equipment
        else:
            return None  # for no UW

    def search_uw_description(self, char_id):
        '''
        gets the UW descrription from a char id
        '''

        equipment = self.search_uw(char_id)
        if equipment:
            equipment = next(equipment)
            uw_id = equipment['EquipmentExclusiveSkillDescriptionId']
            return self.search_id(uw_id, 'EquipmentExclusiveSkillDescriptionMB')
        else:
            return None    

    def search_item(self, id: int, type: int):
        '''
        searches ItemMB
        '''
        obj = filter(lambda x:x["ItemId"]==id and x['ItemType']==type,\
            self.__load_MB('ItemMB'))
        try:
            return next(obj)
        except StopIteration:
            return None

    def find_item(self, ItemId: int, ItemType: int, **_) -> dict:
        '''
        find item by ItemId and ItemType from multiple MB files

        ItemType 14: Runes
        ItemType 17: Containers (Treasue Chests)

        **_ is to catch extra data if using **keyword arguments
        '''
        
        if ItemType == 5:
            return "Fragment"
        elif ItemType == 14:
            item = self.search_id(ItemId, 'SphereMB')
        elif ItemType == 17:
            item = self.search_id(ItemId, 'TreasureChestMB')
        else: # In ItemMB
            item = self.search_item(ItemId, ItemType)

        if item is None:
            print(f'Item not found. Id: {ItemId} Type: {ItemType}')  # add later
        return item

    def search_id_list(self, id_list: Union[List, int], dataMB: str) -> Iterable:
        '''
        search data for multiple id's

        returns an iterable
        '''
        if isinstance(id_list, int):
            id_list = [id_list]

        return filter(lambda x: x['Id'] in id_list, self.__load_MB(dataMB))
    
    def search_tower(self, type: int, floor: int=None)->Iterable:
        '''
        Returns tower data
        Type data:
        Infinity-1, Azure-2, Crimson-3, Emerald-4, Amber-5

        Parameters:
            type: type of tower
            floor[Optional]: specify floor
        '''
        if floor:
            return filter(
                lambda x: x['TowerType']==type and x['Floor']==floor, self.__load_MB('TowerBattleQuestMB'))
        else:
            return filter(lambda x: x['TowerType']==type, self.__load_MB('TowerBattleQuestMB'))
        
    def __find_arcana_group(self, collection: int)->List[dict]:
        arcana_bonus = self.__load_MB('CharacterCollectionLevelMB')
        return list(filter(lambda x: x['CollectionId'] == collection), arcana_bonus)
        
    def search_arcana(self, char_id:int = None)->Iterator:
        '''
        Returns an iterable of lists of an arcana group

        If chars is none, fetch all arcana
        '''
        arcana_chars = self.__load_MB('CharacterCollectionMB')
        
        for arcana in arcana_chars:
            if char_id is None or (char_id in arcana['RequiredCharacterIds']):
                yield self.__find_arcana_group(arcana['Id'])

    def search_equipment(self, char_id=None, **filter_args) ->Iterable:
        '''
        char_id may be passed for simpler UW search
        
        Filter Args
        
        Category: int [1-3]
            1: D-S+ rank gear (Non set-gear)
            2: non UW set-gear
            3: UW
            
        CompositeID: int
            Gotten from CharacterProfileMB
        
        EquipmentLv: int
            Equipment Level
            
        EquippedJobFlags: int [1, 2, 4, 7]
            1: Warrior
            2: Sniper
            3: Sorcerer
            7: All
            
        QualityLv: int [0-4]
            0-1: Non set-gear
            1-4: set-gear
            Note: quality is fixed for set-gear depending on rarity
        
        RarityFlags: int [1-512]
            1: D
            2: C
            4: B
            8: A
            16: S
            32: R
            64: SR
            128: SSR
            256: UR
            512: LR
            
        SlotType
            1: Weapon
            2: Sub
            3: Gauntlet
            4: Helmet
            5: Armor
            6: Shoes
        '''
        
        def filter_func(item):
            return all(item.get(key) == value for key, value in filter_args.items())
        if char_id:
            equipment= self.search_uw(char_id)  # limits to UW
        else:
            equipment = self.__load_MB('EquipmentMB')
        
        return filter(filter_func, equipment)
    
    def search_voiceline(self, char_id):
        voicelines = self.__load_MB('CharacterDetailVoiceMB')
        return list(filter(lambda x: x['CharacterId'] == char_id, voicelines))
    
    def search_memories(self, char_id):
        memories = self.__load_MB('CharacterStoryMB')
        return list(filter(lambda x: x['CharacterId'] == char_id, memories))