from typing import List

from api.schemas.requests import TowerRequest
from api.utils.error import APIError
from api.utils.masterdata import MasterData
from common import enums, schemas

from api.utils.logger import get_logger
logger = get_logger(__name__)

async def parse_quest_enemies(md: MasterData, quest_id: int) -> List[dict]:
    first_enemy = int(f'{enums.EnemyType.BossBattle}{quest_id:05d}01')
    end = int(f'{enums.EnemyType.BossBattle}{quest_id+1:05d}00') # id must be lower than end
    enemy_it = await md.search_consecutive('BossBattleEnemyMB', 'Id', first_enemy)
    enemies = []
    for enemy in enemy_it:
        if enemy['Id'] > end:
            break
        enemies.append(enemy)
    
    return enemies

async def parse_tower_enemies(md: MasterData, enemy_list: List[int]) -> List[dict]:
    first_enemy = enemy_list[0]
    enemy_it = await md.search_consecutive('TowerBattleEnemyMB', 'Id', first_enemy)
    enemies = []
    for enemy in enemy_it:
        if enemy.get('Id') not in enemy_list:
            break
        enemies.append(enemy)
    
    if len(enemy_list) != len(enemies):
        logger.error(f'Enemy data was incorrect: {enemy_list}')

    return enemies

async def get_quest(md: MasterData, quest_id: int) -> schemas.Quest:
    quest_data = await md.search_id(quest_id, 'QuestMB')
    if not quest_data:
        raise APIError(f'Quest id {quest_id} not found')
    enemies = await parse_quest_enemies(md, quest_id)
    return schemas.Quest(**quest_data, enemy_list=enemies)

async def get_tower(md: MasterData, payload: TowerRequest) -> schemas.Tower:
    args = {
        'Floor': payload.floor,
        'TowerType': payload.tower_type
    }
    try:
        tower_data = next(await md.search_filter('TowerBattleQuestMB', **args))
    except StopIteration:
        raise APIError(f'Tower {payload.tower_type} floor {payload.floor} not found')
    enemies = await parse_tower_enemies(md, tower_data.get('EnemyIds'))
    return schemas.Tower(**tower_data, enemy_list=enemies)
