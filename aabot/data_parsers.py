import models

from itertools import chain
from master_data import MasterData
from typing import List
from timezones import convert_from_jst


def parse_fleeting(md: MasterData) -> list[models.GachaPickup]:
    gachacase_data = md.get_MB_data('GachaCaseMB')
    gachacaseui_data = md.get_MB_data('GachaCaseUiMB')
    
    fleeting = []
    id = 1
    gachacaseui_lookup = {item['Id']: item for item in gachacaseui_data}
    for banner in gachacase_data:
        # filter fleeting
        if banner['GachaSelectListType'] == 1 and banner['GachaCaseFlags'] == 1:
            ui_data = gachacaseui_lookup[banner['GachaCaseUiId']]
            gacha = models.GachaPickup(
                id=int(f'1{id:04}'),
                start=convert_from_jst(banner['StartTimeFixJST']),
                end=convert_from_jst(banner['EndTimeFixJST']),
                select_list_type=int(banner['GachaSelectListType']),  # 1
                char_id=int(ui_data['PickUpCharacterId'])
            )
            fleeting.append(gacha)
            id += 1
    return fleeting

def parse_ioc(md: MasterData) -> list[models.GachaPickup]:
    gachadestiny_data = md.get_MB_data('GachaDestinyAddCharacterMB')
    gachaselect_data = md.get_MB_data('GachaSelectListMB')

    ioc = []
    id = 1
    gachaselect_lookup = {item['Id']: item for item in gachaselect_data}
    for banner in gachadestiny_data:
        start_data = gachaselect_lookup[banner['StartGachaSelectListId']]
        end_data = gachaselect_lookup[banner['EndGachaSelectListId']]
        gacha = models.GachaPickup(
            id=int(f'2{id:04}'),
            start=convert_from_jst(start_data['StartTimeFixJST']),
            end=convert_from_jst(end_data['EndTimeFixJST']),
            select_list_type=2,
            char_id=int(banner['CharacterId'])
        )
        ioc.append(gacha)
        id += 1
    return ioc

def parse_iosg(md: MasterData) -> list[models.GachaPickup]:
    gachaselect_data = md.get_MB_data('GachaSelectListMB')

    iosg = []
    id = 1
    iosg_data = filter(lambda item: item['GachaSelectListType'] == 3, gachaselect_data)
    for banner in iosg_data:
        for character in banner['NewCharacterIdList']:
            gacha = models.GachaPickup(
                id=int(f'3{id:04}'),
                start=convert_from_jst(banner['StartTimeFixJST']),
                end=convert_from_jst(banner['EndTimeFixJST']),
                select_list_type=3,
                char_id=int(character)
            )
            iosg.append(gacha)
            id += 1
    return iosg

def parse_gacha(md: MasterData) -> list[models.GachaPickup]:
    fleeting = parse_fleeting(md)
    ioc = parse_ioc(md)
    iosg = parse_iosg(md)
    return list(chain(fleeting, ioc, iosg))


if __name__ == "__main__":
    from common import Server

    md = MasterData()
    d = parse_ioc(md)
    for data in d:
        print(data.nice())

  