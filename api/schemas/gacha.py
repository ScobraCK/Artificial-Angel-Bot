from api.utils.masterdata import MasterData
from common import schemas
from common.enums import GachaType, Server
from common.timezones import check_active

from api.utils.logger import get_logger
logger = get_logger(__name__)

class RunCounter:
    def __init__(self):
        self.run_counts: dict[int, list] = {}

    def get_run_count(self, char_id: int, run: str) -> int:
        if char_id not in self.run_counts:
            self.run_counts[char_id] = []  # initialize char counter
        if run not in self.run_counts[char_id]:  # check if run exists
            self.run_counts[char_id].append(run)  # TODO: sort by date for futureproofing?
        return self.run_counts[char_id].index(run) + 1
    
def parse_run(start, end) -> str: # tuple[str, str]:
    '''Remove hour and second data for run counting'''
    return start[:10]#, end[:10]  # start from start date only

def filter_append_gacha(
    gacha_list: list,
    gacha: schemas.GachaPickup|schemas.GachaChosenGroup,
    char_id: int|None=None,
    is_active=True,
    include_future=False) -> None:
    if char_id:
        if isinstance(gacha, schemas.GachaPickup):
            if gacha.char_id != char_id:
                return
        else:  # chosen or eminence group
            if not any(char_id == banner.char_id for banner in gacha.banners):
                return
        
    if is_active:
        if not check_active(gacha.start, gacha.end, Server.Japan, include_future=include_future):
            return
    
    gacha_list.append(gacha)
        
async def get_gacha(md: MasterData, char_id: int|None=None, is_active=True, include_future=False) -> schemas.GachaPickupBanners:
    gachacase_data = await md.get_MB('GachaCaseMB')
    gachacaseui_data = await md.get_MB('GachaCaseUiMB')
    gachadestiny_data = await md.get_MB('GachaDestinyAddCharacterMB')
    gachaselect_data = await md.get_MB('GachaSelectListMB')
    
    gachacaseui_lookup = {item['Id']: item for item in gachacaseui_data}
    gachaselect_lookup = {item['Id']: item for item in gachaselect_data}
    fleeting_list = []
    ioc_list = []
    iosg_list = []
    chosen_list = []
    eminence_list = []
    
    run_counter = RunCounter()
    eminence_data = []  # defer parsing until IoSG has been parsed for correct run counts

    # Parse fleeting
    for banner in gachacase_data:
        if banner['GachaCaseFlags'] == 1:
            # Normal fleeting banner
            if banner['GachaSelectListType'] == GachaType.Fleeting:  # 1
                ui_data = gachacaseui_lookup[banner['GachaCaseUiId']]
                char = int(ui_data['PickUpCharacterId'])
                run = parse_run(banner['StartTimeFixJST'], banner['EndTimeFixJST'])
                run_count = run_counter.get_run_count(char, run)
                gacha = schemas.GachaPickup(
                    **banner,
                    char_id=char,
                    run_count=run_count
                )
                filter_append_gacha(fleeting_list, gacha, char_id, is_active, include_future)
            # Chosen fleeting banner
            elif banner['GachaSelectListType'] == GachaType.Chosen:  # 4
                banner_id = banner['Id']
                banner_data = gachaselect_lookup.get(banner_id)
                run = parse_run(banner['StartTimeFixJST'], banner['EndTimeFixJST'])
                if not banner_data:
                    continue
                
                gacha_list = []
                for character in banner_data['CharacterIdList']:
                    char = int(character)
                    run_count = run_counter.get_run_count(char, run)
                    gacha = schemas.GachaPickup(
                        start=banner_data['StartTimeFixJST'],
                        end=banner_data['EndTimeFixJST'],
                        gacha_type=GachaType.Chosen,
                        char_id=char,
                        run_count=run_count
                    )
                    gacha_list.append(gacha)
                chosen_group = schemas.GachaChosenGroup(
                    **banner,
                    banners=gacha_list
                )
                filter_append_gacha(chosen_list, chosen_group, char_id, is_active, include_future)
                
            # Chosen Eminence banner
            elif banner['GachaSelectListType'] == GachaType.Eminence:
                eminence_data.append(banner)
                
    # Parse ioc
    for banner in gachadestiny_data:
        start_data = gachaselect_lookup[banner['StartGachaSelectListId']]
        end_data = gachaselect_lookup[banner['EndGachaSelectListId']]
        char = banner['CharacterId']
        run = parse_run(start_data['StartTimeFixJST'], end_data['EndTimeFixJST'])
        run_count = run_counter.get_run_count(char, run)
        gacha = schemas.GachaPickup(
            start=start_data['StartTimeFixJST'],
            end=end_data['EndTimeFixJST'],
            gacha_type=GachaType.IoC,
            char_id=char,
            run_count=run_count
        )
        filter_append_gacha(ioc_list, gacha, char_id, is_active, include_future)

    # Parse iosg
    iosg_data = filter(lambda item: item['GachaSelectListType'] == 3, gachaselect_data)
    for banner in iosg_data:
        for character in banner['NewCharacterIdList']:
            char = int(character)
            run = parse_run(banner['StartTimeFixJST'], banner['EndTimeFixJST'])
            run_count = run_counter.get_run_count(char, run)
            gacha = schemas.GachaPickup(
                **banner,
                char_id=char,
                run_count=run_count
            )
            filter_append_gacha(iosg_list, gacha, char_id, is_active, include_future)
            
    # Parse eminence
    for banner in eminence_data:
        banner_id = banner['Id']
        banner_data = gachaselect_lookup.get(banner_id)
        run = parse_run(banner['StartTimeFixJST'], banner['EndTimeFixJST'])
        if not banner_data:
            continue
        
        gacha_list = []
        for character in banner_data['CharacterIdList']:
            char = int(character)
            run_count = run_counter.get_run_count(char, run)
            gacha = schemas.GachaPickup(
                start=banner_data['StartTimeFixJST'],
                end=banner_data['EndTimeFixJST'],  # different from main banner
                gacha_type=GachaType.Eminence,
                char_id=char,
                run_count=run_count
            )
            gacha_list.append(gacha)
        eminence_group = schemas.GachaEminenceGroup(
            **banner,
            banners=gacha_list
        )
        filter_append_gacha(eminence_list, eminence_group, char_id, is_active, include_future)

    return schemas.GachaPickupBanners(
        fleeting=fleeting_list,
        ioc=ioc_list,
        iosg=iosg_list,
        chosen=chosen_list,
        eminence=eminence_list
    )