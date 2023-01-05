'''
Equipment data
'''
from master_data import MasterData
import common

def get_uw_name(char_id: int, masterdata: MasterData=None):
    if masterdata is None:
        masterdata = MasterData()

    equipment = masterdata.search_uw(char_id)  # get iter
    if equipment:
        equipment = next(equipment)  # equipment is now dict
        return masterdata.search_string_key(equipment.get('NameKey'))
    else:
        return None

def get_uw_descriptions(char_id: int, masterdata: MasterData=None):
    if masterdata is None:
        masterdata = MasterData()
    
    uw_data = masterdata.search_uw_description(char_id)
    if uw_data is None:
        return None
        
    uw = {}
    uw['SSR'] = masterdata.search_string_key(uw_data["Description1Key"])
    uw['UR'] = masterdata.search_string_key(uw_data["Description2Key"])
    uw['LR'] = masterdata.search_string_key(uw_data["Description3Key"])
    return uw
    

if __name__ == "__main__":
    print(get_uw_name(27))