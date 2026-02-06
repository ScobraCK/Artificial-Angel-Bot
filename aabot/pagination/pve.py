from collections import Counter

from discord import  ui
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.pagination.view import BaseContainer
from aabot.utils import api
from aabot.utils.assets import CHARACTER_THUMBNAIL, ENEMY_THUMBNAIL, SOUL_BONUS
from aabot.utils.emoji import to_emoji
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.utils import base_param_text, battle_param_text, from_quest_id, human_format as hf
from common import enums, schemas
from common.database import SessionAA

def get_bonus_url(soul_list):
    c = Counter(soul_list)
    souls = sorted([c[1], c[2], c[3], c[4]], reverse=True)  # normal souls
    light = c[5]
    dark = c[6]
    
    first = souls[0] + light
    bonus = ''
    if first == 3:
        if souls[1] == 2: # 3+2
            bonus = '2'
        else:  # 3
            bonus = '1'
    elif first == 4:
        bonus = '3'
    elif first == 5:
        bonus = '4'
    
    if dark:
        bonus = f'{bonus}_{dark+4}'
        
    bonus_url = SOUL_BONUS.format(bonus=bonus)
    return bonus_url

async def get_enemy_title(enemy: schemas.Enemy, session: AsyncSession, add_reso_text: str|None=None) -> str:
    soul_emj = await to_emoji(session, enemy.element)
    name = f'{soul_emj} Lv.{enemy.level} {enemy.name} [{enums.CharacterRarity(enemy.rarity).name.replace('Plus', '+')}]'
    if add_reso_text:
        name += f'{add_reso_text}'
    return name

def get_enemy_thumbnail(enemy: schemas.Enemy) -> str:
    if enemy.icon_type == enums.UnitIconType.Character:
        icon_url = CHARACTER_THUMBNAIL.format(char_id=enemy.icon_id, qlipha=False)
    elif enemy.icon_type == enums.UnitIconType.EnemyCharacter:
        icon_url = ENEMY_THUMBNAIL.format(enemy_id=enemy.icon_id)
    else:
        icon_url = CHARACTER_THUMBNAIL.format(char_id=enemy.icon_id, qlipha=True)
    return icon_url

async def enemy_basic_text(enemy: schemas.Enemy, session: AsyncSession) -> str:
    return (
        f'{await to_emoji(session, 'atk')} {hf(enemy.battle_params.attack)} '
        f'{await to_emoji(session, 'def')} {hf(enemy.battle_params.defense)}\n'
        f'{await to_emoji(session, 'hp')} {hf(enemy.battle_params.hp)} '
        f'{await to_emoji(session, 'spd')} {enemy.battle_params.speed}\n'
        f'{await to_emoji(session, 'str')} {hf(enemy.base_params.str)} '
        f'{await to_emoji(session, 'dex')} {hf(enemy.base_params.dex)}\n'
        f'{await to_emoji(session, 'mag')} {hf(enemy.base_params.mag)} '
        f'{await to_emoji(session, 'sta')} {hf(enemy.base_params.sta)}'
    )

async def enemy_detail_ui(enemy: schemas.Enemy, cs: schemas.CommonStrings) -> BaseContainer:
    async with SessionAA() as session:
        container = (
            BaseContainer(f'### {await get_enemy_title(enemy, session)}')
            .add_item(ui.Section(
                ui.TextDisplay(f'**Base Parameters**\n{base_param_text(enemy.base_params, cs)}'),
                ui.TextDisplay(f'**Battle Parameters**\n{battle_param_text(enemy.battle_params, cs)}'),
                ui.TextDisplay(
                    f'**Skills**\n'
                    f'```json\n'
                    f'Actives: {enemy.actives}\n'
                    f'Passives: {enemy.passives}\n'
                    f'UW Rarity: {enums.ItemRarity(enemy.uw_rarity).name}\n'
                    f'```'
                ),
                accessory=ui.Thumbnail(get_enemy_thumbnail(enemy))
            ))
        )
    return container
        
def find_resonance_idx(def_list: list) -> tuple[int, int]:
    '''returns the indices of the lowest and highest defense in the list'''
    if len(def_list) < 2:
        return (-1, -1)
    min_ind = def_list.index(min(def_list))
    max_ind = def_list.index(max(def_list))
    return (min_ind, max_ind)

async def quest_ui(quest_id: int, language: enums.LanguageOptions, cs: schemas.CommonStrings) -> dict:
    content_map = {}
    quest_resp = await api.fetch_api(
        api.QUEST_PATH.format(quest_id=quest_id),
        query_params={'language': language},
        response_model=schemas.Quest,
    )
    quest = quest_resp.data
    
    async with SessionAA() as session:
        main_container = BaseContainer(f'### Stage {from_quest_id(quest.quest_id)} (ID: {quest.quest_id})')
        # loop once to get BP and resonance
        bp = 0
        def_list = []
        for i, enemy in enumerate(quest.enemy_list):
            def_list.append(enemy.battle_params.defense)
            bp += enemy.bp
        min_ind, max_ind = find_resonance_idx(def_list)
        
        main_container.add_item(ui.TextDisplay(f'**BP:** {bp:,}\n{await to_emoji(session, 'red_orb')}×{quest.red_orb}/d')).add_item(ui.Separator())
        for i, enemy in enumerate(quest.enemy_list):
            resonance_text = None
            if min_ind == i:
                resonance_text = f' {await to_emoji(session, 'resonance')}{await to_emoji(session, 'down')}'
            elif max_ind == i:
                resonance_text = f' {await to_emoji(session, 'resonance')}{await to_emoji(session, 'up')}'
            main_container.add_item(
                ui.Section(
                    ui.TextDisplay(
                        f'**{await get_enemy_title(enemy, session, resonance_text)}**\n'
                        f'{await enemy_basic_text(enemy, session)}'
                    ),
                    accessory=ui.Thumbnail(get_enemy_thumbnail(enemy))
                )
            ).add_item(ui.Separator(visible=False))
        content_map['Quest Overview'] = main_container.add_version(quest_resp.version)

        # Enemy Details
        enemy_pages = []
        for enemy in quest.enemy_list:
            enemy_pages.append((await enemy_detail_ui(enemy, cs)).add_version(quest_resp.version))
        content_map['Enemy Details'] = enemy_pages
    return content_map

async def tower_ui(floor: int, towertype: enums.TowerType, language: enums.LanguageOptions, cs: schemas.CommonStrings) -> dict:
    content_map = {}
    tower_resp = await api.fetch_api(
        api.TOWER_PATH,
        query_params={
            'floor': floor,
            'tower_type': towertype,
            'language': language
        },
        response_model=schemas.Tower,
    )
    tower = tower_resp.data
    fixed_rewards = tower.fixed_rewards
    first_time_rewards = tower.first_rewards

    async with SessionAA() as session:
        main_container = BaseContainer(f'### Tower of {towertype.name} - Floor {tower.floor}')
        # loop once to get BP and resonance
        bp = 0
        def_list = []
        for i, enemy in enumerate(tower.enemy_list):
            def_list.append(enemy.battle_params.defense)
            bp += enemy.bp
        min_ind, max_ind = find_resonance_idx(def_list)

        main_text = f'**BP:** {bp:,}'
        
        ic = ItemCounter()
        if fixed_rewards:
            ic.add_items(fixed_rewards)
            main_text += f'\n**Fixed Rewards:**\n{' '.join(await ic.get_total_strings())}'
        if first_time_rewards:
            ic.clear()
            ic.add_items(first_time_rewards)
            main_text += f'\n**First Time Rewards:**\n{' '.join(await ic.get_total_strings())}'
        main_container.add_item(ui.TextDisplay(main_text)).add_item(ui.Separator())
        
        for i, enemy in enumerate(tower.enemy_list):
            resonance_text = None
            if min_ind == i:
                resonance_text = f' {await to_emoji(session, 'resonance')}{await to_emoji(session, 'down')}'
            elif max_ind == i:
                resonance_text = f' {await to_emoji(session, 'resonance')}{await to_emoji(session, 'up')}'
            main_container.add_item(
                ui.Section(
                    ui.TextDisplay(
                        f'**{await get_enemy_title(enemy, session, resonance_text)}**\n'
                        f'{await enemy_basic_text(enemy, session)}'
                    ),
                    accessory=ui.Thumbnail(get_enemy_thumbnail(enemy))
                )
            ).add_item(ui.Separator(visible=False))
        content_map['Tower Overview'] = main_container.add_version(tower_resp.version)
        
        # Enemy Details
        enemy_pages = []
        for enemy in tower.enemy_list:
            enemy_pages.append((await enemy_detail_ui(enemy, cs)).add_version(tower_resp.version))
        content_map['Enemy Details'] = enemy_pages
    return content_map
