'''
def insert_gacha(db: Session, md: masterdata.MasterData=None):
    if md is None:
        md = masterdata.MasterData()
        
    gachacase_data = md.get_MB('GachaCaseMB')
    gachacaseui_data = md.get_MB('GachaCaseUiMB')
    gachadestiny_data = md.get_MB_data('GachaDestinyAddCharacterMB')
    gachaselect_data = md.get_MB_data('GachaSelectListMB')

    # fleeting
    gachacaseui_lookup = {item['Id']: item for item in gachacaseui_data}
    for banner in gachacase_data:
        if banner['GachaSelectListType'] == 1 and banner['GachaCaseFlags'] == 1:  # limited banner
            ui_data = gachacaseui_lookup[banner['GachaCaseUiId']]
                # gacha_orm = gacha.GachaPickupORM()

def parse_fleeting(md: masterdata.MasterData) -> list[GachaPickup]:
    gachacase_data = md.get_MB_data('GachaCaseMB')
    gachacaseui_data = md.get_MB_data('GachaCaseUiMB')
    
    fleeting = []
    id = 1
    gachacaseui_lookup = {item['Id']: item for item in gachacaseui_data}
    for banner in gachacase_data:
        # filter fleeting
        if banner['GachaSelectListType'] == 1 and banner['GachaCaseFlags'] == 1:
            ui_data = gachacaseui_lookup[banner['GachaCaseUiId']]
            gacha = GachaPickup(
                **banner,
                gacha_id=int(f'1{id:04}'),
                char_id=int(ui_data['PickUpCharacterId'])
            )
            fleeting.append(gacha)
            id += 1
    return fleeting

def parse_ioc(md: masterdata.MasterData) -> list[GachaPickup]:
    gachadestiny_data = md.get_MB_data('GachaDestinyAddCharacterMB')
    gachaselect_data = md.get_MB_data('GachaSelectListMB')

    ioc = []
    id = 1
    gachaselect_lookup = {item['Id']: item for item in gachaselect_data}
    for banner in gachadestiny_data:
        start_data = gachaselect_lookup[banner['StartGachaSelectListId']]
        end_data = gachaselect_lookup[banner['EndGachaSelectListId']]
        gacha = GachaPickup(
            id=int(f'2{id:04}'),
            start=start_data['StartTimeFixJST'],
            end=end_data['EndTimeFixJST'],
            select_list_type=2,
            char_id=banner['CharacterId']
        )
        ioc.append(gacha)
        id += 1
    return ioc

def parse_iosg(md: masterdata.MasterData) -> list[GachaPickup]:
    gachaselect_data = md.get_MB_data('GachaSelectListMB')

    iosg = []
    id = 1
    iosg_data = filter(lambda item: item['GachaSelectListType'] == 3, gachaselect_data)
    for banner in iosg_data:
        for character in banner['NewCharacterIdList']:
            gacha = GachaPickup(
                **banner,
                id=int(f'3{id:04}'),
                char_id=int(character)
            )
            iosg.append(gacha)
            id += 1
    return iosg

def parse_gacha(md: masterdata.MasterData) -> list[GachaPickup]:
    fleeting = parse_fleeting(md)
    ioc = parse_ioc(md)
    iosg = parse_iosg(md)
    return list(chain(fleeting, ioc, iosg))'''