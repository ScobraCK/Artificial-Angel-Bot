'''
Equipment data
'''
from master_data import MasterData
from typing import Optional
import common
from dataclasses import dataclass
import re
from helper import reverse_dict_search
from itertools import chain
from items import Item, get_item_list
### for UW skill descriptions ###

def get_uw_name(
    char_id: int, 
    masterdata: MasterData, 
    lang: Optional[common.Language]='enUS'):

    equipment = masterdata.search_uw(char_id)  # get iter
    if equipment:
        equipment = next(equipment)  # equipment is now dict
        return masterdata.search_string_key(equipment.get('NameKey'), language=lang)
    else:
        return None

def get_uw_descriptions(
    char_id: int, 
    masterdata: MasterData, 
    lang: Optional[common.Language]='enUS'):
    '''
    {SSR: desc1, UR: desc2, LR: desc3}
    '''
    
    uw_data = masterdata.search_uw_description(char_id)
    if uw_data is None:
        return None
        
    uw = {}
    uw['SSR'] = masterdata.search_string_key(uw_data["Description1Key"], language=lang)
    uw['UR'] = masterdata.search_string_key(uw_data["Description2Key"], language=lang)
    uw['LR'] = masterdata.search_string_key(uw_data["Description3Key"], language=lang)
    return uw


## temp location for params

def get_param(param_info, masterdata:MasterData, lang: Optional[common.Language]='enUS', as_string=False):
    '''
    Returns parameter, value
    as_string: if True, returns the change value formatted as string. Else returns raw value.
    '''

    if param_type := param_info.get('BattleParameterType'):
        parameter_key = common.battle_parameter_key_map[param_type]
        parameter = masterdata.search_string_key(parameter_key, lang)
    else:
       param_type = param_info.get('BaseParameterType') 
       parameter_key = common.base_parameter_key_map[param_type]
       parameter = masterdata.search_string_key(parameter_key, lang)
     
    change_type =  param_info['ChangeParameterType']
    if as_string:
        if param_type in common.battle_parameter_percentage_id or change_type == 2:
            value = f"{param_info['Value']/100:.1f}%"
        else:
            value = f"{int(param_info['Value']):,}"
    else:
        value = param_info['Value']   
    return parameter, value

### Gear data API beta ###

@dataclass
class Equipment:
    name: str
    icon: int
    equip_type: str  # gun, sword, book, head etc
    rarity: str
    level: int
    stat_type: str
    stat: int
    basestat: int
    bonus_parameters: int
    is_uw: bool
    upgrade_type: int # 1: weapon 2: other
    upgrade_level: int
    evolution_id: int
    composite_id: int
    # set only
    set_name: Optional[int]=None
    set_effect: Optional[list]=None
    # UW only
    uw_bonus: Optional[list]=None
    char_id: Optional[int]=None

def get_set_effect(set_id, masterdata: MasterData, lang: Optional[common.Language]='enUS'):
    '''
    returns set effect strings
    
    name: str
    effect_list[
        Tuple[set_requirement, parameter, value]
            set_requirement: str
            parameter: str
            value: str
        ]
    '''
    set_data = masterdata.search_id(set_id, "EquipmentSetMB")
    
    name = masterdata.search_string_key(set_data.get("NameKey"), language=lang)
    effect_list = []
    
    for effect in set_data.get('EffectList'):
        if param_info := effect.get('BaseParameterChangeInfo'):
            param, value = get_param(param_info, masterdata, lang,as_string=True)
        else:
            param, value = get_param(effect.get('BattleParameterChangeInfo'), masterdata, lang,as_string=True)
        set_count = effect['RequiredEquipmentCount']    
        set_requirement = masterdata.search_string_key('[EquipmentSet]', language=lang).format(set_count)
        
        effect_list.append((set_requirement, param, value))  
    
    return name, effect_list  

def get_uw_bonus(effect_id, masterdata: MasterData, lang: Optional[common.Language]='enUS'):
    uw_effect_data = masterdata.search_id(effect_id, 'EquipmentExclusiveEffectMB')
    
    effect_list = []
    
    for param_info in chain(uw_effect_data.get('BaseParameterChangeInfoList') or [], uw_effect_data.get('BattleParameterChangeInfoList') or []):
        param, value = get_param(param_info, masterdata, lang, as_string=True)
        effect_list.append((param, value))

    return effect_list

def calc_stats(basestat, upgrade_level, masterdata: MasterData):
    if upgrade_level == 0:
        return int(basestat)
    
    coef_data = masterdata.search_id(upgrade_level, 'EquipmentReinforcementParameterMB')
    coef = coef_data['ReinforcementCoefficient']
    return int(basestat * coef)

def split_equip_tokens(equipment_str: str):
    res = re.match(r'(?P<rarity>[a-zA-Z]+)(?P<level>\d+)?(?P<upgrade>\+\d+)?', equipment_str)
    
    return res.groupdict() if res else None

def get_equipment_from_str(
    slot: int,
    equipment_str,
    masterdata: MasterData,
    lang: Optional[common.Language]='enUS',
    *, 
    char_id: int=None,
    job=7
    ):
    
    search_args = split_equip_tokens(equipment_str)
    if search_args is None:
        return None
    
    if search_args['level'] is None and search_args['upgrade'] is None:
        return None
    
    # parse rarity
    search_args['rarity'] = search_args['rarity'].upper()  # to match case with rarity dict   
    if search_args['rarity'] == 'SP':  # S+
        search_args['rarity'] = 'S'
        search_args['quality'] = 1  # add quality
    search_args['rarity'] = reverse_dict_search(common.equip_rarity, search_args['rarity'])
        
    if search_args['upgrade']:
        search_args['upgrade'] = search_args['upgrade'].removeprefix('+')
        if search_args['level'] is None:  # level is ommited
            search_args['level'] = search_args['upgrade']  # considered upgrade is max
    else:
        search_args['upgrade'] = 0  # case where upgrade is 0
        
    search_args['level'] = int(search_args['level'])
    search_args['upgrade'] = int(search_args['upgrade'])
    search_args['char_id'] = char_id
    search_args['job'] = job
        
    return get_equipment(slot, masterdata=masterdata, lang=lang, **search_args)

def get_equipment(
    slot: int,
    rarity: int,
    level: int,
    upgrade: int,
    masterdata: MasterData, 
    lang: Optional[common.Language]='enUS',
    *, 
    char_id:int=None,
    quality=None,
    job=7
    ):
    '''
    Grabs full equipment data and sends in JSON format
    
    Input:
        slot
        rarity
        level
        upgrade
        [character]: for UW
        [quality]: only usecase would be for S+ rarity gear (rarity 32 with quality of 1)
        [job]: only needed if type = 1 (weapon) and character is None
    '''
    
    if upgrade > level:
        return None  # need error raise here
    
    search_args = {
        'RarityFlags': rarity,
        'EquipmentLv': level,
    }
    if quality:
        search_args['QualityLv'] = quality
    if not char_id:
        search_args['SlotType'] = slot
        search_args['EquippedJobFlags'] = job
        search_args['ExclusiveEffectId'] = 0
    
    equipment_iter = masterdata.search_equipment(char_id=char_id, **search_args)
    
    equipment_data = next(equipment_iter)

    try:
        next(equipment_iter)
        return None  # temp return to check if multiple equipment
    except StopIteration:
        pass
    
    rarity = common.equip_rarity[rarity]
    if rarity == "S" and quality == 1:
        rarity = 'S+'
        
    equip_type = common.EquipSlot((slot, equipment_data['EquippedJobFlags'])).name
    
    stat_type, basestat = get_param(equipment_data.get('BattleParameterChangeInfo'), masterdata, lang)
    
    equipment = Equipment(
        name=masterdata.search_string_key(equipment_data['NameKey'], lang),
        icon=equipment_data['IconId'],
        equip_type=equip_type,
        rarity=rarity,
        level=level,
        stat_type=stat_type, 
        stat=calc_stats(basestat, upgrade, masterdata),
        basestat=int(basestat),
        bonus_parameters=equipment_data['AdditionalParameterTotal'],
        upgrade_type=equipment_data['EquipmentReinforcementMaterialId'],
        upgrade_level=upgrade,
        evolution_id=equipment_data['EquipmentEvolutionId'],
        composite_id=equipment_data['CompositeId'],
        is_uw=bool(char_id),
        char_id=char_id
    )
    
    if set_id := equipment_data['EquipmentSetId']:
        equipment.set_name, equipment.set_effect = get_set_effect(set_id, masterdata, lang)
    
    if char_id:
        equipment.uw_bonus = get_uw_bonus(equipment_data['ExclusiveEffectId'], masterdata, lang)
    
    return equipment


def get_enhance_cost(start, end, id, masterdata: MasterData, lang: Optional[common.Language]='enUS', composite_id=None):
    total_items = {}
    enhance_data = masterdata.search_id(id, 'EquipmentEvolutionMB')
    
    if composite_id:  # createion material
        composite_data = masterdata.search_id(composite_id, 'EquipmentCompositeMB')
        shard_count = composite_data['RequiredFragmentCount']
        composite_item_list = get_item_list(masterdata, composite_data['RequiredItemList'], lang)
        composite_item_list.append(Item('Fragment', shard_count, composite_id, 5))
        for item in composite_item_list:
            if total_items.get(item.name):
                total_items[item.name] += item
            else:
                total_items[item.name] = item

    for enhance_info in enhance_data['EquipmentEvolutionInfoList']:
        before = enhance_info['BeforeEquipmentLv']
        after = enhance_info['AfterEquipmentLv']
        
        if after > end:
            break
        if start <= before:
            item_list = get_item_list(masterdata, enhance_info['RequiredItemList'],lang)
            for item in item_list:
                if total_items.get(item.name):
                    total_items[item.name] += item
                else:
                    total_items[item.name] = item
                    
    return total_items

def get_reinforcement_cost(start, end, id, masterdata: MasterData, lang: Optional[common.Language]='enUS'):
    total_items = {}
    
    if end > 0:  # no 0 in data
        reinforcement_data = masterdata.search_id(id, 'EquipmentReinforcementMaterialMB')
        for reinforcement_info in reinforcement_data['ReinforcementMap']:
            lv = reinforcement_info['Lv']
            if lv == end:
                break
            if start <= lv:
                item_list = get_item_list(masterdata, reinforcement_info['RequiredItemList'],lang)
                for item in item_list:
                    if total_items.get(item.name):
                        total_items[item.name] += item
                    else:
                        total_items[item.name] = item
    return total_items
    
def get_upgrade_costs(
    masterdata: MasterData, equip1: Equipment, equip2: Equipment=None, lang: Optional[common.Language]='enUS'):
    if equip2:
        if (equip1.upgrade_type != equip2.upgrade_type or equip1.equip_type != equip2.equip_type or equip1.is_uw != equip2.is_uw):
            return None
        
        level1 = equip1.level
        upgrade1 = equip1.upgrade_level
        rarity1 = equip1.rarity
        level2 = equip2.level
        upgrade2 = equip2.upgrade_level
        rarity2 = equip2.rarity
        comp = None
    else:
        level1 = 180
        upgrade1 = 0
        rarity1 = 'SSR' if equip1.is_uw else 'UR'  # UW or Micheal gear
        level2 = equip1.level
        upgrade2 = equip1.upgrade_level
        rarity2 = equip1.rarity
        comp = equip1.composite_id
            
    if level1 > level2:
        return None
    if upgrade1 > upgrade2:
        return None
    if reverse_dict_search(common.equip_rarity, rarity1) > reverse_dict_search(common.equip_rarity, rarity2):
        return None

    dew = 0
    if equip1.is_uw or rarity2 == 'LR':
        if rarity1 == 'SSR' and rarity2 == 'UR':
            dew = 15
        if rarity1 == 'SSR' and rarity2 == 'LR':
            dew = 65
        if rarity1 == 'UR' and rarity2 == 'LR':
            dew = 50
               
    total_cost = get_enhance_cost(level1, level2, equip1.evolution_id, masterdata, lang, composite_id=comp)
    reinforcement_cost = get_reinforcement_cost(upgrade1, upgrade2, equip1.upgrade_type, masterdata, lang)
    
    if reinforcement_cost:
        for item in reinforcement_cost.values():
            if total_cost.get(item.name):
                total_cost[item.name] += item
            else:
                total_cost[item.name] = item
    
    # dew data
    if dew != 0:
        dews = get_item_list(masterdata, [{"ItemCount": dew,"ItemId": 1,"ItemType": 24}], lang)[0]
        total_cost[dews.name] = dews
    
    return total_cost

if __name__ == "__main__":
    md = MasterData()
    from pprint import pprint
    # # res = md.search_equipment(**{'EquipmentLv': 1, 'RarityFlags': 8, 'SlotType': 5})
    # # 
    # # # pprint(res)
    
    from common import EquipSlot
    equip_type = EquipSlot.Sword
    string = 'lr+370'
    char = 63
    
    # pprint(get_equipment_from_str(1, string[1], md, char_id=char, job=equip_type.value.EquippedJobFlags))
    # # pprint(common.EquipSlot((4, 7)).name)
    equip = get_equipment_from_str(1, string, md, char_id=char, job=equip_type.value.EquippedJobFlags)
    items = get_upgrade_costs(md, equip)
                              
    for item in items.values():
        print(item)

'''
equipment search (500+)
[charid][rarity:2][type:1][level:4]

rarity
7: R
8 SR
9 SSR
10 UR
11 LR

type
1: sword
2: pistol
3: tome
4: acc
...

'''