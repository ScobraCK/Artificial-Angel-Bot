# from fastapi import Request
from datetime import datetime
from pydantic import (
    AliasChoices, AliasPath, BeforeValidator, BaseModel, ConfigDict, Field,
    ModelWrapValidatorHandler, TypeAdapter,
    field_serializer, model_validator,
)
from pydantic.json_schema import SkipJsonSchema
from typing import Annotated, Any, Generic, Literal, Self, TypeVar, Union

from common import enums

# Common
class APIBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name = True)  # populate by name default true

T = TypeVar("T")
class APIResponse(APIBaseModel, Generic[T]):
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(examples=['version'])
    data: T

    @classmethod
    def create(cls, request, data: T) -> "APIResponse[T]":  # API (request: fastapi.Request)
        return cls(
            version=request.app.state.md.version,
            data=data,
        )

    @classmethod
    def parse(cls, data: dict, data_type: type[T]) -> "APIResponse[T]":  # AAbot
        parsed_data = TypeAdapter(data_type).validate_python(data["data"])
        return cls(timestamp=data["timestamp"], version=data["version"], data=parsed_data)

class Parameter(APIBaseModel):
    parameter_type: Literal['Base', 'Battle']
    type: int = Field(..., validation_alias=AliasChoices('BaseParameterType', 'BattleParameterType'))
    change_type: int = Field(..., alias='ChangeParameterType') 
    value: int = Field(..., alias='Value')
    
    @model_validator(mode='before')
    @classmethod
    def set_param_type(cls, data: Any) -> Any:
        if data and data.get('parameter_type') is None:  # only set once. Check data for validation checks in case of union (NoneType may be passed)
            if data.get('BaseParameterType') is not None:
                data['parameter_type'] = 'Base'
            else:
                data['parameter_type'] = 'Battle'
        return data

# class BaseParameterModel(APIBaseModel):   
#     type: enums.BaseParameter = Field(..., validation_alias='BaseParameterType')
#     change_type: int = Field(..., alias='ChangeParameterType') 
#     value: int = Field(..., alias='Value')

# class BattleParameterModel(APIBaseModel):
#     type: enums.BattleParameter = Field(..., validation_alias='BattleParameterType')
#     change_type: int = Field(..., alias='ChangeParameterType') 
#     value: int = Field(..., alias='Value')

# Used to show an amount of item. Cost, reward etc
class ItemCount(APIBaseModel):
    item_id: int = Field(..., validation_alias='ItemId', examples=[1])
    item_type: int = Field(..., validation_alias='ItemType', examples=[3])
    count: int = Field(..., validation_alias='ItemCount', examples=[1000])

# Character
class Character(APIBaseModel):
    char_id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    title: str|None = Field(..., validation_alias='Name2Key')
    element: enums.Element = Field(..., validation_alias='ElementType')
    rarity: enums.CharacterRarity = Field(..., validation_alias='RarityFlags')
    job: enums.Job = Field(..., validation_alias='JobFlags')
    speed: int = Field(..., validation_alias=AliasPath('InitialBattleParameter', 'Speed'))
    uw: str|None = Field(...)
    attack_type: enums.NormalSkill = Field(..., validation_alias='NormalSkillId')
    actives: list[int] = Field(..., validation_alias='ActiveSkillIds')
    passives: list[int] = Field(..., validation_alias='PassiveSkillIds')

class Profile(APIBaseModel):
    char_id: int = Field(..., validation_alias='Id')
    birthday: int = Field(..., validation_alias='Birthday')
    height: int = Field(..., validation_alias='Height')
    weight: int = Field(..., validation_alias='Weight')
    blood_type: enums.BloodType = Field(..., validation_alias='BloodType')
    gacha_message: str|None = Field(..., validation_alias='GachaResultMessage2Key')
    voiceJP: str = Field(..., validation_alias='CharacterVoiceJPKey')
    voiceUS: str|None = Field(..., validation_alias='CharacterVoiceUSKey')
    vocalJP: str = Field(..., validation_alias='VocalJPKey')
    vocalUS: str|None = Field(..., validation_alias='VocalUSKey')
    
    @model_validator(mode='after')
    def fill_US_va(self)->Any:
        if self.voiceUS is None:
            self.voiceUS = f'[CharacterProfileVoiceUS{self.char_id}]'
        
        if self.vocalUS is None:
            self.vocalUS = f'[CharacterProfileVocalUS{self.char_id}]'

        return self

class Name(BaseModel):
    '''Simple model for only character name'''
    char_id: int
    name: str
    title: str|None

class Lament(APIBaseModel):
    char_id: int = Field(validation_alias='Id')
    nameJP: str = Field(..., validation_alias='LamentJPKey')
    nameUS: str = Field(..., validation_alias='LamentUSKey')
    youtubeJP: str|None = Field(..., validation_alias=AliasPath('MovieJpUrl', 'jaJP'))
    youtubeUS: str|None = Field(..., validation_alias=AliasPath('MovieUsUrl', 'enUS'))
    lyricsJP: str = Field(..., validation_alias='LyricsJPKey')  # lyrics shown are translated for selected language
    lyricsUS: str = Field(..., validation_alias='LyricsUSKey')

class Voiceline(APIBaseModel):
    category: enums.VoiceCategory = Field(..., validation_alias='CharacterVoiceCategory')
    unlock: enums.VoiceUnlock = Field(..., validation_alias='UnlockCondition')
    unlock_quest: int = Field(..., validation_alias='UnlockQuestId')
    sort_order: int = Field(..., validation_alias='SortOrder')
    subtitle: str|None = Field(..., validation_alias='SubtitleKey')
    button_text: str = Field(..., validation_alias='UnlockedVoiceButtonTextKey')

class CharacterVoicelines(APIBaseModel):
    char_id: int = Field(...,)
    voicelines: list[Voiceline] = Field(...,)

class Memory(APIBaseModel):
    episode_id: int = Field(..., validation_alias='EpisodeId') 
    level: int = Field(..., validation_alias='Level')
    rarity: enums.CharacterRarity = Field(..., validation_alias='RarityFlags')
    reward: list[ItemCount] = Field(..., validation_alias='RewardItemList')
    title: str = Field(..., validation_alias='TitleKey')
    text: str = Field(..., validation_alias='TextKey')

class CharacterMemories(APIBaseModel):
    char_id: int
    memories: list[Memory]

# Equipment
class Equipment(APIBaseModel):
    equip_id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    icon_id: int = Field(..., validation_alias='IconId')
    slot: enums.EquipSlot = Field(..., validation_alias='SlotType')
    job: enums.Job = Field(..., validation_alias='EquippedJobFlags')
    rarity: enums.ItemRarity = Field(..., validation_alias='RarityFlags')
    quality: int = Field(..., validation_alias='QualityLv')
    level: int = Field(..., validation_alias='EquipmentLv')
    bonus_parameters: int = Field(..., validation_alias='AdditionalParameterTotal')
    basestat: Parameter = Field(..., validation_alias='BattleParameterChangeInfo')
    evolution_id: int = Field(..., validation_alias='EquipmentEvolutionId')
    composite_id: int = Field(..., validation_alias='CompositeId')
    equipment_set: Union["EquipmentSet", None] = None

class UniqueWeapon(Equipment):
    character_id: int
    uw_bonus: list[Parameter]
    uw_descriptions: 'UWDescriptions'

class SetEffect(APIBaseModel):
    equipment_count: int = Field(..., validation_alias='RequiredEquipmentCount')
    parameter: Parameter = Field(...)
    
    # Data has both BaseParameterChangeInfo or BattleParameterChangeInfo but one is empty and need to use non empty one
    @model_validator(mode='before')
    @classmethod
    def set_param(cls, data: Any) -> Any:
        if data.get('parameter') is None:  # parameter is already set during transformer
            if data.get('BaseParameterChangeInfo') is not None:
                data['parameter'] = data.get('BaseParameterChangeInfo')
            else:
                data['parameter'] = data.get('BattleParameterChangeInfo')
        return data

class EquipmentSet(APIBaseModel):
    id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    set_effects: list[SetEffect] = Field(..., validation_alias='EffectList')

class UWDescriptions(APIBaseModel):
    SSR: str = Field(..., validation_alias='Description1Key')
    UR: str = Field(..., validation_alias='Description2Key')
    LR: str = Field(..., validation_alias='Description3Key')

class EquipmentUpgradeLevel(APIBaseModel):
    upgrade_level: int
    coefficient: float
    cost: list[ItemCount]

class EquipmentUpgradeData(APIBaseModel):
    is_weapon: bool
    upgrades: list[EquipmentUpgradeLevel]  

class EquipmentEnhanceLevel(APIBaseModel):
    before_level: int = Field(..., validation_alias='BeforeEquipmentLv')
    after_level: int = Field(..., validation_alias='AfterEquipmentLv')
    cost: list[ItemCount] = Field(..., validation_alias='RequiredItemList')

class EquipmentSynthesis(APIBaseModel):
    rarity: enums.ItemRarity
    cost: list[ItemCount]

class EquipmentEnhanceRarity(APIBaseModel):
    before_rarity: enums.ItemRarity
    after_rarity: enums.ItemRarity
    cost: list[ItemCount]

class EquipmentCosts(APIBaseModel): 
    equipment: Equipment|UniqueWeapon
    upgrade_costs: EquipmentUpgradeData = Field(..., description='Cost to upgrade equipment')
    synthesis_costs: EquipmentSynthesis|None = Field(None, description='Cost to create equipment')
    enhance_costs: list[EquipmentEnhanceLevel] = Field(..., description='Cost to increase equipment level')
    rarity_enhance_costs: list[EquipmentEnhanceRarity] = Field(..., description='Cost to upgrade equipment rarity')

# Events
class GachaPickup(APIBaseModel):
    start: str = Field(..., validation_alias='StartTimeFixJST', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='JST')
    end: str = Field(..., validation_alias='EndTimeFixJST', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='JST')
    gacha_type: enums.GachaType = Field(..., validation_alias='GachaSelectListType')
    run_count: int
    char_id: int

class GachaChosenGroup(APIBaseModel):
    banner_id: int = Field(..., validation_alias='Id', description='Discriminator for grouping of chosen banners')
    start: str = Field(..., validation_alias='StartTimeFixJST', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='JST')
    end: str = Field(..., validation_alias='EndTimeFixJST', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='JST')
    banners: list[GachaPickup]

class GachaBanners(APIBaseModel):
    fleeting: list[GachaPickup]
    ioc: list[GachaPickup]
    iosg: list[GachaPickup]
    chosen: list[GachaChosenGroup]

# Groups
class GrandBattleDate(APIBaseModel):
    start: str = Field(..., validation_alias='StartTime', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='Local date')
    end: str = Field(..., validation_alias='EndTime', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='Local date')

class Group(APIBaseModel):
    group_id: int = Field(..., validation_alias='Id')
    server: enums.Server = Field(..., validation_alias='TimeServerId')
    start: str = Field(..., validation_alias='StartTime', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='Local date. Group start date.')
    end: str = Field(..., validation_alias='EndTime', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='Local date. Group end date.')
    worlds: list[int] = Field(..., validation_alias='WorldIdList')
    grand_battle: list[GrandBattleDate] = Field(..., validation_alias='GrandBattleDateTimeList')
    league_start: str = Field(..., validation_alias='StartLegendLeagueDateTime', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='Local date')
    league_end: str = Field(..., validation_alias='EndLegendLeagueDateTime', pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', description='Local date')

Groups = TypeAdapter(list[Group])

# Items
class ItemBase(APIBaseModel):
    id: int = Field(..., validation_alias='Id')
    item_id: int = Field(..., validation_alias='ItemId')
    item_type: enums.ItemType = Field(..., validation_alias='ItemType')
    name: str = Field(..., validation_alias='NameKey')
    description: str = Field(..., validation_alias='DescriptionKey')
    icon: int = Field(..., validation_alias='IconId')
    rarity: enums.ItemRarity = Field(..., validation_alias=AliasChoices('ItemRarityFlags', 'RarityFlags'))
    max_count: int = Field(0, validation_alias='MaxItemCount')

class Rune(ItemBase):
    item_id: int = Field(..., validation_alias='Id')
    item_type: enums.ItemType = enums.ItemType.Sphere
    parameter: Parameter = Field(...)
    category: enums.RuneType = Field(..., validation_alias='CategoryId')
    level: int = Field(..., validation_alias='Lv')
    sphere_type: int = Field(..., ge=0, le=3, validation_alias='SphereType', description='Size of rune icon')
    icon: int|SkipJsonSchema[None] = Field(None)  # added in validation, icon = {Category:02}{SphereType:02}

    @model_validator(mode='wrap')
    @classmethod
    def set_param_and_icon(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Any:
        if isinstance(data, dict) and data.get('parameter') is None:  # only set once, validated as Rune(BaseModel) during translation
            if data.get('BaseParameterChangeInfo') is not None:
                data['parameter'] = data.get('BaseParameterChangeInfo')
            else:
                data['parameter'] = data.get('BattleParameterChangeInfo')  # Either one should always be present

        rune = handler(data)
        if rune.icon is None:
            rune.icon = int(f'{rune.category.value:02}{rune.sphere_type:02}')

        return rune

class TreasureChest(ItemBase):
    item_type: enums.ItemType = enums.ItemType.TreasureChest
    bulk_enabled: bool = Field(..., validation_alias='BulkUseEnabled')
    min_open_count: int = Field(..., validation_alias='MinOpenCount')
    secondary_frame_num: int = Field(..., validation_alias='SecondaryFrameNum')
    secondary_fram_type: int = Field(..., validation_alias='SecondaryFrameType')  # skipped enum 0-4
    lottery_type: int = Field(..., validation_alias='TreasureChestLotteryType')
    item_id_list: list[int] = Field(..., validation_alias='TreasureChestItemIdList')
    # start, end exists but is null for most

class CharacterItem(ItemBase):
    # Used for gacha log
    item_id: int = Field(..., validation_alias='Id')
    item_type: enums.ItemType = enums.ItemType.Character
    icon: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    title: str|None = Field(..., validation_alias='Name2Key')
    description: str = 'Character'

# Insert CharacterMB to schema directly
class CharacterFragment(ItemBase):
    item_id: int = Field(..., validation_alias='Id', description='Charater Id')
    item_type: enums.ItemType = enums.ItemType.CharacterFragment
    char_name: str = Field(..., validation_alias='NameKey')
    char_title: str|None = Field(..., validation_alias='Name2Key')
    name: str = '[CommonItemCharacterFragment]'
    description: str = '[ItemTypeCharacterFragmentDescription]'
    icon: int = Field(..., validation_alias='Id')

    @field_serializer('name')
    def format_name(self, name: str) -> str:
        return name.format(self.char_name)
    
    @field_serializer('description')
    def format_description(self, description: str) -> str:
        name = self.char_name
        if self.char_title:
            name = f'[{self.char_title}] {name}'
            
        return description.format(name, 60)
    
class EquipmentSetMaterial(ItemBase):
    item_id: int = Field(..., validation_alias='Id')
    item_type: enums.ItemType = enums.ItemType.EquipmentSetMaterial
    lv: int = Field(..., validation_alias='Lv')
    treasure_chest_id: int = Field(..., validation_alias='TreasureChestId', description='Weapon adamantite Id')
    quest_id_list: list[int] = Field(..., validation_alias='QuestIdList')

class EquipmentFragment(ItemBase):
    # EquipmentCompositeMB
    # icon need to get from EquipmentMB
    item_id: int = Field(..., validation_alias='Id')
    item_type: enums.ItemType = enums.ItemType.EquipmentFragment
    equip_id: int = Field(..., validation_alias='EquipmentId')
    required_count: int = Field(..., validation_alias='RequiredFragmentCount')
    name: str = '[CommonItemEquipmentFragmentFormat]'
    equip_name: str = Field(...)  # From EquipmentMB
    description: str = '[ItemTypeEquipmentFragmentDescription]'
    cost: list[ItemCount] = Field(..., validation_alias='RequiredItemList', description='Cost to enhance equipment')
    
    @field_serializer('name')
    def format_name(self, name: str) -> str:
        return name.format(self.equip_name)

    @field_serializer('description')
    def format_description(self, description: str) -> str:
        return description.format(self.equip_name, self.required_count)

type Item = EquipmentFragment|CharacterItem|CharacterFragment|EquipmentSetMaterial|Rune|TreasureChest|ItemBase

# PvE
class BaseParameters(APIBaseModel):
    str: int = Field(validation_alias='Muscle')
    dex: int = Field(validation_alias='Energy')
    mag: int = Field(validation_alias='Intelligence')
    sta: int = Field(validation_alias='Health')

class BattleParameters(APIBaseModel):
    hp: int = Field(..., validation_alias="HP")
    attack: int = Field(..., validation_alias="AttackPower")
    defense: int = Field(..., validation_alias="Defense")
    def_break: int = Field(..., validation_alias="DefensePenetration")
    speed: int = Field(..., validation_alias="Speed")
    pmdb: int = Field(..., validation_alias="DamageEnhance")
    acc: int = Field(..., validation_alias="Hit")
    crit: int = Field(..., validation_alias="Critical")
    crit_dmg: int = Field(..., validation_alias="CriticalDamageEnhance")
    debuff_acc: int = Field(..., validation_alias="DebuffHit")
    counter: int = Field(..., validation_alias="DamageReflect")
    pdef: int = Field(..., validation_alias="PhysicalDamageRelax")
    mdef: int = Field(..., validation_alias="MagicDamageRelax")
    evade: int = Field(..., validation_alias="Avoidance")
    crit_res: int = Field(..., validation_alias="CriticalResist")
    pcut: int = Field(..., validation_alias="PhysicalCriticalDamageRelax")
    mcut: int = Field(..., validation_alias="MagicCriticalDamageRelax")
    debuff_res: int = Field(..., validation_alias="DebuffResist")
    hp_drain: int = Field(..., validation_alias="HpDrain")
    
class Enemy(APIBaseModel):
    enemy_id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    bp: int = Field(..., validation_alias='BattlePower')
    icon_type: enums.UnitIconType = Field(..., validation_alias='UnitIconType')
    icon_id: int = Field(..., validation_alias='UnitIconId')
    element: enums.Element = Field(..., validation_alias='ElementType')
    rarity: enums.CharacterRarity = Field(..., validation_alias='CharacterRarityFlags')
    job: enums.Job = Field(..., validation_alias='JobFlags')
    level: int = Field(..., validation_alias='EnemyRank')
    base_params: BaseParameters = Field(..., validation_alias='BaseParameter')
    battle_params: BattleParameters = Field(..., validation_alias='BattleParameter')
    attack_type: enums.NormalSkill = Field(..., validation_alias='NormalSkillId')
    actives: list[int] = Field(..., validation_alias='ActiveSkillIds')
    passives: list[int] = Field(..., validation_alias='PassiveSkillIds')
    uw_rarity: enums.ItemRarity = Field(..., validation_alias='ExclusiveEquipmentRarityFlags')

class Quest(APIBaseModel):
    quest_id: int = Field(..., validation_alias='Id')
    chapter: int = Field(..., validation_alias='ChapterId')
    enemy_list: list[Enemy]
    gold: int = Field(..., validation_alias='GoldPerMinute')
    red_orb: int = Field(..., validation_alias='PotentialJewelPerDay')
    population: int = Field(..., validation_alias='Population')
    # min_green_orb: int
    # min_exp

class Tower(APIBaseModel):
    tower_id: int = Field(..., validation_alias='Id')
    tower_type: enums.TowerType = Field(..., validation_alias='TowerType')
    floor: int = Field(..., validation_alias='Floor')
    fixed_rewards: list[ItemCount]|None = Field(..., validation_alias='BattleRewardsConfirmed')
    first_rewards: list[ItemCount]|None = Field(..., validation_alias='BattleRewardsFirst')
    enemy_list: list[Enemy]

# Skills
class Skills(APIBaseModel):
    character: int
    actives: list['ActiveSkill']
    passives: list['PassiveSkill']
    uw_descriptions: Union['UWDescriptions', None]

class ActiveSkill(APIBaseModel):
    id: int = Field(..., validation_alias='Id')
    name: Annotated[str, BeforeValidator(lambda v: v or '')] = Field(validation_alias='NameKey', description='null converted to empty string')
    skill_infos: list['SkillInfo'] = Field(..., validation_alias='ActiveSkillInfos')
    condition: str = Field(..., validation_alias='ActiveSkillConditions')
    init_cooltime: int = Field(..., validation_alias='SkillInitCoolTime')
    max_cooltime: int = Field(..., validation_alias='SkillMaxCoolTime')

class PassiveSkill(APIBaseModel):
    id: int = Field(..., validation_alias='Id')
    name: Annotated[str, BeforeValidator(lambda v: v or '')] = Field(validation_alias='NameKey', description='null converted to empty string')
    skill_infos: list['SkillInfo'] = Field(..., validation_alias='PassiveSkillInfos')

class PassiveSubSkill(APIBaseModel):
    trigger: enums.PassiveTrigger = Field(..., validation_alias='PassiveTrigger')
    init_cooltime: int = Field(..., validation_alias='SkillCoolTime')
    max_cooltime: int = Field(..., validation_alias='SkillMaxCoolTime')
    group_id: int = Field(..., validation_alias='PassiveGroupId')
    subskill_id: int = Field(..., validation_alias='SubSetSkillId')

class SkillInfo(APIBaseModel):
    order_number: int = Field(..., validation_alias='OrderNumber')
    description: Annotated[str, BeforeValidator(lambda v: v or '')] = Field(validation_alias='DescriptionKey', description='null converted to empty string')
    level: int = Field(..., validation_alias='CharacterLevel')
    uw_rarity: enums.ItemRarity = Field(..., validation_alias='EquipmentRarityFlags')
    blessing_item: int = Field(..., validation_alias='BlessingItemId')
    subskill: list[int]|list[PassiveSubSkill] = Field(..., validation_alias=AliasChoices('SubSetSkillIds', 'PassiveSubSetSkillInfos'))

# DB Models
class Player(BaseModel):
    id: int
    world_id: int
    name: str
    bp: int
    rank: int
    quest_id: int
    tower_id: int
    azure_tower_id: int|None
    crimson_tower_id: int|None
    emerald_tower_id: int|None
    amber_tower_id: int|None
    icon_id: int
    guild_id: int|None
    guild_join_time: int|None
    guild_position: int|None
    prev_legend_league_class: int|None
    timestamp: int

    class Config:
        from_attributes = True

class PlayerRankInfo(BaseModel):
    id: int
    name: str
    server: int
    world: int
    bp: int|None
    rank: int|None
    quest_id: int|None
    tower_id: int|None
    azure_tower_id: int|None
    crimson_tower_id: int|None
    emerald_tower_id: int|None
    amber_tower_id: int|None
    timestamp: int

    class Config:
        from_attributes = True

class Guild(BaseModel):
    id: int
    world_id: int
    name: str
    bp: int
    level: int
    stock: int
    exp: int
    num_members: int
    leader_id: int
    description: str|None
    free_join: bool
    bp_requirement: int
    timestamp: int

    class Config:
        from_attributes = True

class GuildRankInfo(BaseModel):
    id: int
    name: str
    server: int
    world: int
    bp: int
    timestamp: int

    class Config:
        from_attributes = True

class StringKey(BaseModel):
    key: str = Field(examples=['[CharacterName1]'])
    jajp: str|None = Field(None, example="モニカ")
    kokr: str|None = Field(None, example="모니카")
    enus: str|None = Field(None, example="Monica")
    zhtw: str|None = Field(None, example="莫妮卡")
    dede: str|None = Field(None, example="Monica")
    esmx: str|None = Field(None, example="Mónica")
    frfr: str|None = Field(None, example="Monica")
    idid: str|None = Field(None, example="Monica")
    ptbr: str|None = Field(None, example="Mônica")
    ruru: str|None = Field(None, example="Моника")
    thth: str|None = Field(None, example="โมนิก้า")
    vivn: str|None = Field(None, example="Monica")
    zhcn: str|None = Field(None, example="莫妮卡")

    class Config:
        from_attributes = True

class CharacterDBModel(BaseModel):
    id: int = Field(validation_alias='Id')
    speed: int = Field(validation_alias=AliasPath('InitialBattleParameter', 'Speed'))
    element: int = Field(validation_alias='ElementType')
    job: int = Field(validation_alias='JobFlags')
    base_rarity: Literal['N', 'R', 'SR']

    class Config:
        from_attributes = True
        populate_by_name = True

# Common Enum Strings
class CommonStrings(BaseModel):
    base_param: dict[enums.BaseParameter, str] = Field({
        1: '[BaseParameterTypeMuscle]',
        2: '[BaseParameterTypeEnergy]',
        3: '[BaseParameterTypeIntelligence]',
        4: '[BaseParameterTypeHealth]',
    })
    battle_param: dict[enums.BattleParameter, str] = Field({
        1: '[BattleParameterTypeHp]',
        2: '[BattleParameterTypeAttackPower]',
        3: '[BattleParameterTypePhysicalDamageRelax]',
        4: '[BattleParameterTypeMagicDamageRelax]',
        5: '[BattleParameterTypeHit]',
        6: '[BattleParameterTypeAvoidance]',
        7: '[BattleParameterTypeCritical]',
        8: '[BattleParameterTypeCriticalResist]',
        9: '[BattleParameterTypeCriticalDamageEnhance]',
        10: '[BattleParameterTypePhysicalCriticalDamageRelax]',
        11: '[BattleParameterTypeMagicCriticalDamageRelax]',
        12: '[BattleParameterTypeDefensePenetration]',
        13: '[BattleParameterTypeDefense]',
        14: '[BattleParameterTypeDamageEnhance]',
        15: '[BattleParameterTypeDebuffHit]',
        16: '[BattleParameterTypeDebuffResist]',
        17: '[BattleParameterTypeDamageReflect]',
        18: '[BattleParameterTypeHpDrain]',
        19: '[BattleParameterTypeSpeed]',
    })
    job: dict[int, str] = Field({   # enums.Job
        1: '[JobFlagsWarrior]',
        2: '[JobFlagsSniper]',
        4: '[JobFlagsSorcerer]',
        7: 'All'  # All job flags
    })
    element: dict[enums.Element, str] = Field({
        1: '[ElementTypeBlue]',
        2: '[ElementTypeRed]',
        3: '[ElementTypeGreen]',
        4: '[ElementTypeYellow]',
        5: '[ElementTypeLight]',
        6: '[ElementTypeDark]',
    })
    equip_type: dict[enums.EquipSlot, str] = Field({
        1: '[EquipmentSlotTypeWeapon]',
        2: '[EquipmentSlotTypeSub]',
        3: '[EquipmentSlotTypeHelmet]',
        4: '[EquipmentSlotTypeArmor]',
        5: '[EquipmentSlotTypeGauntlet]',
        6: '[EquipmentSlotTypeShoes]',
    })
    weapon_type: dict[enums.Job, str] = Field({
        1: '[EquipmentSlotTypeSword]',
        2: '[EquipmentSlotTypePistol]',
        4: '[EquipmentSlotTypeTome]',
    })
    rune_type: dict[enums.RuneType, str] = Field({
        1: '[SphereCategoryTypeMuscle]',
        2: '[SphereCategoryTypeEnergy]',
        3: '[SphereCategoryTypeIntelligence]',
        4: '[SphereCategoryTypeAttackPower]',
        5: '[SphereCategoryTypeDamageEnhance]',
        6: '[SphereCategoryTypeHit]',
        7: '[SphereCategoryTypeCritical]',
        8: '[SphereCategoryTypeDebuffHit]',
        9: '[SphereCategoryTypeSpeed]',
        10: '[SphereCategoryTypeHealth]',
        11: '[SphereCategoryTypeHp]',
        12: '[SphereCategoryTypePhysicalDamageRelax]',
        13: '[SphereCategoryTypeMagicDamageRelax]',
        14: '[SphereCategoryTypeAvoidance]',
        15: '[SphereCategoryTypeCriticalResist]',
        16: '[SphereCategoryTypeDebuffResist]',
    })

    class Config:
        use_enum_values = True
