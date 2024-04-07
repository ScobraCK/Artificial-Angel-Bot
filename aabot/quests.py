from typing import List
from master_data import MasterData
import re
from common import Tower

def convert_from_stage(quest: str)->int:
    '''
    Converts [chapter]-[stage] to quest id
    returns None if invalid

    Max stages
    Chapter 1: 12
    Chapter 2: 20
    Chapter 3: 24
    Chapter 4+: 28
    '''
    if quest.isnumeric():
        return int(quest)
    try:
        chap, stage = tuple(map(int, (re.split('[ -/]', quest, maxsplit=2))))
    except ValueError:
        return None
    
    if not (0 < stage <= 40):
        return None
    if chap == 1:
        return (stage if stage <= 12 else None)
    elif chap == 2:
        return (stage + 12 if stage <= 20 else None) 
    elif chap == 3:
        return (stage + 32 if stage <= 24 else None)
    elif chap < 27:
        return (chap-2) * 28 + stage  # 1-3 is 28*2 stages
    else:
        return 700 + (chap-27)*40 + stage  # 26-28 is 700

def convert_to_stage(quest_id: int)->str:
    '''
    Converts quest id to [chapter]-[stage]

    Max stages
    Chapter 1: 12
    Chapter 2: 20
    Chapter 3: 24
    Chapter 4+: 28
    Chapter 27+: 40
    '''
    if quest_id > 700:
        chap, stage = divmod(quest_id-700, 40)
        if stage==0:
            chap += -1
            stage = 40
        return f"{chap+27}-{stage}"
    elif quest_id > 56:
        chap, stage = divmod(quest_id, 28)
        if stage==0:
            chap += -1
            stage = 28
        return f"{chap+2}-{stage}"
    elif quest_id > 32: # chapter 3
        return f"3-{quest_id-32}"
    elif quest_id > 12: # chapter 2
        return f"2-{quest_id-12}"
    else: # chapter 1
        return f"1-{quest_id}"



def get_quest(master: MasterData, quest: int)->dict:
    '''
    Get from QuestMB
    '''
    return master.search_id(quest, 'QuestMB')

def get_quest_enemy(master: MasterData, quest: int)->List[dict]:
    enemy_ids = []
    for i in range(1,6):
        enemy_ids.append(int(f"20{quest:04d}{i:02d}"))  # ex) quest=1, enemy no.1, 20_0001_01
    return list(master.search_id_list(enemy_ids, 'BossBattleEnemyMB'))

def get_tower_floor(master: MasterData, floor: int, type: Tower):
    try:
        return next(master.search_tower(type.value, floor))
    except StopIteration:
        return None

def get_tower_enemy(master: MasterData, enemy_ids: int)->List[dict]:
    return list(master.search_id_list(enemy_ids, 'TowerBattleEnemyMB'))

if __name__ == "__main__":
    a = [1, 5, 5, 5, 5]
    from collections import Counter
    c = Counter(a)
    souls = sorted([c[1], c[2], c[3], c[4]], reverse=True)  # normal souls
    light = c[5]
    dark = c[6]

    print(souls)