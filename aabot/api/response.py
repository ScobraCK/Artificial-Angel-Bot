from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass
from typing import List, Optional, Union, TypeVar, Generic, Type, get_origin
from datetime import datetime

T = TypeVar('T')

@dataclass
class APIResponse(Generic[T]):
    timestamp: datetime
    version: str
    data: T

    @classmethod
    def parse(cls, data: dict, data_type: Type[T]) -> "APIResponse[T]":
        parsed_data = TypeAdapter(data_type).validate_python(data["data"])
        return cls(timestamp=data["timestamp"], version=data["version"], data=parsed_data)

# Subclasses
@dataclass
class BaseParameterModel:
    type: str
    change_type: int
    value: int

@dataclass
class BattleParameterModel:
    type: str
    change_type: int
    value: int
    is_percentage: bool

@dataclass
class BaseParameters:
    str: int
    dex: int
    mag: int
    sta: int

@dataclass
class BattleParameters:
    hp: int
    attack: int
    defense: int
    def_break: int
    speed: int
    pmdb: int
    acc: int
    crit: int
    crit_dmg: int
    debuff_acc: int
    counter: int
    pdef: int
    mdef: int
    evade: int
    crit_res: int
    pcut: int
    mcut: int
    debuff_res: int
    hp_drain: int

@dataclass
class ItemCount:
    item_id: int
    item_type: int
    count: int

@dataclass
class EquipmentSet:
    id: int
    name: str
    set_effects: List['SetEffect']

@dataclass
class SetEffect:
    equipment_count: int
    parameter: Union[BaseParameterModel, BattleParameterModel]

@dataclass
class SkillInfo:
    order_number: int
    description: str
    level: int
    uw_rarity: Optional[str]
    blessing_item: int
    subskill: List[Union[int, 'PassiveSubSkill']]

@dataclass
class PassiveSubSkill:
    trigger: str
    init_cooltime: int
    max_cooltime: int
    group_id: int
    subskill_id: int

@dataclass
class UWDescriptions:
    SSR: str
    UR: str
    LR: str

@dataclass
class Voiceline:
    category: str
    unlock: Optional[str]
    unlock_quest: int
    sort_order: int
    subtitle: Optional[str]
    button_text: str

# Final response models
@dataclass
class Character:
    char_id: int
    name: str
    title: Optional[str]
    element: str
    rarity: str
    job: str
    speed: int
    uw: Optional[str]
    attack_type: str
    actives: List[int]
    passives: List[int]

@dataclass
class Profile:
    char_id: int
    birthday: int
    height: int
    weight: int
    blood_type: str
    gacha_message: Optional[str]
    voiceJP: str
    voiceUS: Optional[str]
    vocalJP: str
    vocalUS: Optional[str]

@dataclass
class CharacterDBModel:
    char_id: int
    speed: int
    element: int
    job: int
    base_rarity: str

@dataclass
class StringDBModel:
    key: str
    jajp: Optional[str]
    kokr: Optional[str]
    enus: Optional[str]
    zhtw: Optional[str]
    dede: Optional[str]
    esmx: Optional[str]
    frfr: Optional[str]
    idid: Optional[str]
    ptbr: Optional[str]
    ruru: Optional[str]
    thth: Optional[str]
    vivn: Optional[str]
    zhcn: Optional[str]

@dataclass
class Equipment:
    equip_id: int
    name: str
    icon_id: int
    slot: str
    job: str
    rarity: str
    quality: int
    level: int
    bonus_parameters: int
    basestat: BattleParameterModel
    equipment_set: Optional[EquipmentSet]
    
@dataclass
class UniqueWeapon(Equipment):
    character_id: int
    uw_bonus: List[Union[BaseParameterModel, BattleParameterModel]]
    uw_descriptions: UWDescriptions

@dataclass
class EquipmentUpgradeLevel:
    upgrade_level: int
    coefficient: float
    cost: List[ItemCount]

@dataclass
class EquipmentUpgradeData:
    is_weapon: bool
    upgrades: List[EquipmentUpgradeLevel]   

@dataclass
class EquipmentEnhanceLevel:
    before_level: int
    after_level: int
    cost: List[ItemCount]

@dataclass
class EquipmentSynthesis:
    rarity: str
    cost: List[ItemCount]
   
@dataclass
class EquipmentEnhanceRarity:
    before_rarity: str
    after_rarity: str
    cost: List[ItemCount] 

@dataclass
class EquipmentCosts: 
    equipment: Equipment|UniqueWeapon
    upgrade_costs: EquipmentUpgradeData
    synthesis_costs: Optional[EquipmentSynthesis]
    enhance_costs: List[EquipmentEnhanceLevel]
    rarity_enhance_costs: List[EquipmentEnhanceRarity]

@dataclass
class Quest:
    quest_id: int
    chapter: int
    gold: int
    red_orb: int
    population: int
    enemy_list: List['Enemy']

@dataclass
class Tower:
    tower_id: int
    tower_type: str
    floor: int
    fixed_rewards: Optional[List['ItemCount']]
    first_rewards: Optional[List['ItemCount']]
    enemy_list: List['Enemy']

@dataclass
class Enemy:
    enemy_id: int
    name: str
    bp: int
    icon_type: int
    icon_id: int
    element: str
    rarity: str
    job: str
    level: int
    base_params: BaseParameters
    battle_params: BattleParameters
    attack_type: str
    actives: List[int]
    passives: List[int]
    uw_rarity: Optional[str]

@dataclass
class Lament:
    char_id: int
    nameJP: str
    nameUS: str
    youtubeJP: str
    youtubeUS: str
    lyricsJP: str
    lyricsJP_translated: Optional[str]
    lyricsUS: str

@dataclass
class PassiveSkill:
    id: int
    name: str
    skill_infos: List[SkillInfo]

@dataclass
class ActiveSkill:
    id: int
    name: str
    skill_infos: List[SkillInfo]
    condition: str
    init_cooltime: int
    max_cooltime: int

@dataclass
class Skills:
    character: int
    actives: List[ActiveSkill]
    passives: List[PassiveSkill]
    uw_descriptions: Optional[UWDescriptions]

@dataclass
class Name:
    char_id: int
    name: str
    title: Optional[str]

@dataclass
class CharacterVoicelines:
    char_id: int
    voicelines: List[Voiceline]

@dataclass
class Memory:
    episode_id: int
    level: int
    rarity: str
    reward: List[ItemCount]
    title: str
    text: str

@dataclass
class CharacterMemories:
    char_id: int
    memories: List[Memory]

@dataclass
class ItemBase:
    id: int
    item_id: int
    item_type: str
    name: str
    description: str
    icon: int
    rarity: Optional[str]
    max_count: int

@dataclass
class Rune(ItemBase):
    '''Item type 14, runes'''
    parameter: Union[BaseParameterModel, BattleParameterModel]
    category: str
    level: int

Item = Union[Rune, ItemBase]

@dataclass
class PlayerDBModel:
    id: int
    world_id: int
    name: str
    auto_bp: int
    bp: Optional[int]
    rank: int
    quest_id: int
    tower_id: int
    azure_tower_id: int
    crimson_tower_id: int
    emerald_tower_id: int
    amber_tower_id: int
    icon_id: int
    guild_id: Optional[int]
    guild_join_time: Optional[int]
    guild_position: Optional[int]
    prev_legend_league_class: Optional[int]
    timestamp: int
    
@dataclass
class PlayerRankInfo:
    name: str
    server: int
    world: int
    bp: Optional[int]
    quest_id: Optional[int]
    tower_id: Optional[int]
    azure_tower_id: Optional[int]
    crimson_tower_id: Optional[int]
    emerald_tower_id: Optional[int]
    amber_tower_id: Optional[int]
    timestamp: int

@dataclass
class GuildDBModel:
    id: int
    world_id: int
    name: str
    bp: int
    level: int
    stock: int
    exp: int
    num_members: int
    leader_id: int
    description: Optional[str]
    free_join: bool
    bp_requirement: int
    timestamp: int

@dataclass
class GuildRankInfo:
    name: str
    server: int
    world: int
    bp: int
    timestamp: int

@dataclass
class GachaPickup:
    start: int
    end: int
    gacha_type: int
    run_count: int
    char_id: int