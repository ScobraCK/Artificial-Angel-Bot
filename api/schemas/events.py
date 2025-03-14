from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List

from api.utils.enums import GachaType
from api.utils.masterdata import MasterData
from api.utils.timezones import get_current
from api.schemas import validators

from api.utils.logger import get_logger
logger = get_logger(__name__)

class GachaPickup(BaseModel):
    start: int = Field(..., validation_alias='StartTimeFixJST', description='Start time in UNIX timestamp')
    end: int = Field(..., validation_alias='EndTimeFixJST', description='End time in UNIX timestamp')
    gacha_type: GachaType = Field(..., validation_alias='GachaSelectListType')
    run_count: int
    char_id: int

    _convert_date = field_validator('start', 'end', mode='before')(validators.val_date_jst)

    class Config:
        populate_by_name = True

class GachaRequest(BaseModel):
    char_id: Optional[int] = Field(None, description='Character ID to filter by')
    is_active: bool = Field(True, description='Filter by currently active banners')

class RunCounter:
    def __init__(self):
        self.run_counts: Dict[int, List] = {}

    def get_run_count(self, char_id: int, run: tuple) -> int:
        if char_id not in self.run_counts:
            self.run_counts[char_id] = []  # initialize char counter
        if run not in self.run_counts[char_id]:  # check if run exists
            self.run_counts[char_id].append(run)
        return self.run_counts[char_id].index(run) + 1

async def parse_gacha(md: MasterData) -> list[GachaPickup]:
    gachacase_data = await md.get_MB('GachaCaseMB')
    gachacaseui_data = await md.get_MB('GachaCaseUiMB')
    gachadestiny_data = await md.get_MB('GachaDestinyAddCharacterMB')
    gachaselect_data = await md.get_MB('GachaSelectListMB')

    gacha_list = []
    run_counter = RunCounter()

    # Parse fleeting
    gachacaseui_lookup = {item['Id']: item for item in gachacaseui_data}
    for banner in gachacase_data:
        if banner['GachaSelectListType'] == 1 and banner['GachaCaseFlags'] == 1:
            ui_data = gachacaseui_lookup[banner['GachaCaseUiId']]
            char = int(ui_data['PickUpCharacterId'])
            run = (banner['StartTimeFixJST'], banner['EndTimeFixJST'])
            run_count = run_counter.get_run_count(char, run)
            gacha = GachaPickup(
                **banner,
                char_id=char,
                run_count=run_count
            )
            gacha_list.append(gacha)

    # Parse ioc
    gachaselect_lookup = {item['Id']: item for item in gachaselect_data}
    for banner in gachadestiny_data:
        start_data = gachaselect_lookup[banner['StartGachaSelectListId']]
        end_data = gachaselect_lookup[banner['EndGachaSelectListId']]
        char = banner['CharacterId']
        run = (start_data['StartTimeFixJST'], end_data['EndTimeFixJST'])
        run_count = run_counter.get_run_count(char, run)
        gacha = GachaPickup(
            start=start_data['StartTimeFixJST'],
            end=end_data['EndTimeFixJST'],
            gacha_type=GachaType.IoC,
            char_id=char,
            run_count=run_count
        )
        gacha_list.append(gacha)

    # Parse iosg
    iosg_data = filter(lambda item: item['GachaSelectListType'] == 3, gachaselect_data)
    for banner in iosg_data:
        for character in banner['NewCharacterIdList']:
            char = int(character)
            run = (banner['StartTimeFixJST'], banner['EndTimeFixJST'])
            run_count = run_counter.get_run_count(char, run)
            gacha = GachaPickup(
                **banner,
                char_id=char,
                run_count=run_count
            )
            gacha_list.append(gacha)

    return gacha_list

async def get_gacha(md: MasterData, char_id: int=None, is_active=True) -> list[GachaPickup]:
    gacha_list = await parse_gacha(md)
    filtered = []
    for gacha in gacha_list:
        if char_id:
            if gacha.char_id != char_id:
                continue    
        if is_active:
            current = get_current()
            if gacha.end < current or gacha.start > current:
                continue 
        filtered.append(gacha)
    return filtered