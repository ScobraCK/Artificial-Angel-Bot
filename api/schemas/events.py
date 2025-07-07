from api.utils.masterdata import MasterData
from common import schemas
from common.enums import GachaType, Server
from common.timezones import check_active

from api.utils.logger import get_logger
logger = get_logger(__name__)

class RunCounter:
    def __init__(self):
        self.run_counts: dict[int, list] = {}

    def get_run_count(self, char_id: int, run: tuple) -> int:
        if char_id not in self.run_counts:
            self.run_counts[char_id] = []  # initialize char counter
        if run not in self.run_counts[char_id]:  # check if run exists
            self.run_counts[char_id].append(run)
        return self.run_counts[char_id].index(run) + 1

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
        else:
            if not any(char_id == banner.char_id for banner in gacha.banners):
                return
        
    if is_active:
        if not check_active(gacha.start, gacha.end, Server.Japan, include_future=include_future):
            return
    
    gacha_list.append(gacha)
        
async def get_gacha(md: MasterData, char_id: int|None=None, is_active=True, include_future=False) -> schemas.GachaBanners:
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
    
    run_counter = RunCounter()

    # Parse fleeting
    for banner in gachacase_data:
        if banner['GachaCaseFlags'] == 1:
            # Normal fleeting banner
            if banner['GachaSelectListType'] == GachaType.Fleeting:  # 1
                ui_data = gachacaseui_lookup[banner['GachaCaseUiId']]
                char = int(ui_data['PickUpCharacterId'])
                run = (banner['StartTimeFixJST'], banner['EndTimeFixJST'])
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
                run = (banner['StartTimeFixJST'], banner['EndTimeFixJST'])
                if not banner_data:
                    continue
                
                gacha_list = []
                for character in banner_data['CharacterIdList']:
                    char = int(character)
                    run_count = run_counter.get_run_count(char, run)
                    gacha = schemas.GachaPickup(
                        start=banner['StartTimeFixJST'],
                        end=banner['EndTimeFixJST'],
                        gacha_type=GachaType.Chosen,
                        char_id=char,
                        run_count=run_count
                    )
                    gacha_list.append(gacha)
                chosen_group = schemas.GachaChosenGroup(
                    banner_id=banner_id,
                    start=banner['StartTimeFixJST'],
                    end=banner['EndTimeFixJST'],
                    banners=gacha_list
                )
                filter_append_gacha(chosen_list, chosen_group, char_id, is_active, include_future)

    # Parse ioc
    for banner in gachadestiny_data:
        start_data = gachaselect_lookup[banner['StartGachaSelectListId']]
        end_data = gachaselect_lookup[banner['EndGachaSelectListId']]
        char = banner['CharacterId']
        run = (start_data['StartTimeFixJST'], end_data['EndTimeFixJST'])
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
            run = (banner['StartTimeFixJST'], banner['EndTimeFixJST'])
            run_count = run_counter.get_run_count(char, run)
            gacha = schemas.GachaPickup(
                **banner,
                char_id=char,
                run_count=run_count
            )
            filter_append_gacha(iosg_list, gacha, char_id, is_active, include_future)

    return schemas.GachaBanners(
        fleeting=fleeting_list,
        ioc=ioc_list,
        iosg=iosg_list,
        chosen=chosen_list
    )