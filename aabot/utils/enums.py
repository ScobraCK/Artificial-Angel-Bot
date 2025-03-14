from enum import Enum, Flag, StrEnum, IntEnum, IntFlag
from collections import namedtuple

class Language(StrEnum):
    enus = 'enus'
    jajp = 'jajp'
    kokr = 'kokr'
    zhtw = 'zhtw'
    # ArEg = 'ArEg'
    # DeDe = 'DeDe'
    # EsMx = 'EsMx'
    # FrFr = 'FrFr'
    # IdId = 'IdId'
    # PtBr = 'Ptbr'
    # RuRu = 'RuRu'
    # ThTh = 'ThTh'
    # ViVn = 'ViVn'
    # ZhCn = 'ZhCn'

class Server(IntEnum):
    Japan = 1
    Korea = 2
    Asia = 3
    America = 4
    Europe = 5
    Global = 6


class ItemType(Enum):
    '''Non-official enum naming'''
    FreeDiamond = 1  # CurrencyFree
    PaidDiamond = 2  # Currencypaid
    Gold = 3
    Equipment = 4
    EquipmentFragment = 5
    Character = 6
    CharacterFragment = 7
    DungeonBattleRelic = 8
    EquipmentSetMaterial = 9
    BossReapTicket = 10  # QuestQuickTicket
    CharacterTrainingMaterial = 11
    EquipmentReinforcementItem = 12
    ExchangePlaceItem = 13
    Rune = 14  # Sphere
    AugmentBottle = 15  # MatchlessSacredTreasureExpItem AugmentBottle
    GachaTicket = 16
    TreasureChest = 17
    TreasureChestKey = 18
    BossChallengeTicket = 19
    TowerBattleTicket = 20
    DungeonRecoveryItem = 21
    PlayerExp = 22
    FriendPoint = 23
    EquipmentRarityCrystal = 24
    LevelLinkExp = 25
    GuildFame = 26
    GuildExp = 27
    ActivityMedal = 28
    VipExp = 29
    PanelGetJudgmentItem = 30
    UnlockPanelGridItem = 31
    PanelUnlockItem = 32
    MusicTicket = 33
    SpecialIcon = 34
    IconFragment = 35
    GuildTowerJobReinforcementMaterial = 36
    RealPrizeGoods = 37
    RealPrizeDigital = 38
    PopularityVote = 39
    LuckyChanceGachaTicket = 40
    ChatBalloon = 41
    EventExchangePlaceItem = 50
    StripeCoupon = 1001

EquipTypeTuple = namedtuple('EquipTypeTuple', ['slot', 'job'])

class EquipType(Enum):
    '''Job 7 is None for api'''
    Sword = EquipTypeTuple(1, 1)
    Gun = EquipTypeTuple(1, 2)
    Tome = EquipTypeTuple(1, 4)
    Accessory = EquipTypeTuple(2, None)
    Gauntlet = EquipTypeTuple(3, None)
    Helmet = EquipTypeTuple(4, None)
    Chest = EquipTypeTuple(5, None)
    Boots = EquipTypeTuple(6, None)

class EquipRarity(IntFlag):
    D = 1
    C = 2
    B = 4
    A = 8
    S = 16
    R = 32
    SR = 64
    SSR = 128
    UR = 256
    LR = 512

class Tower(IntEnum):
    Infinity = 1
    Azure = 2
    Crimson = 3
    Emerald = 4
    Amber = 5

######################################################
# if flag/enum has a string key
class _EnumMixin:
    def __new__(cls, value, str_key=None):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.str_key = str_key
        return obj

class _Enum(_EnumMixin, Enum):
    pass

class _Flag(_EnumMixin, Flag):
    @property
    def str_keys(self):
        return [flag.str_key for flag in self.__class__ if self & flag]


class Job(_Flag):
    Warrior = (1, '[JobFlagsWarrior]')
    Sniper = (2, '[JobFlagsSniper]')
    Sorcerer = (4, '[JobFlagsSorcerer]')


equip_type = {
    (1, Job.Warrior): '[EquipmentSlotTypeSword]',
    (1, Job.Sniper): '[EquipmentSlotTypePistol]',
    (1, Job.Sorcerer): '[EquipmentSlotTypeTome]',
    (2, Job.Warrior | Job.Sniper | Job.Sorcerer): '[EquipmentSlotTypeSub]',
    (3, Job.Warrior | Job.Sniper | Job.Sorcerer): '[EquipmentSlotTypeHelmet]',
    (4, Job.Warrior | Job.Sniper | Job.Sorcerer): '[EquipmentSlotTypeArmor]',
    (5, Job.Warrior | Job.Sniper | Job.Sorcerer): '[EquipmentSlotTypeGauntlet]',
    (6, Job.Warrior | Job.Sniper | Job.Sorcerer): '[EquipmentSlotTypeShoes]',
}

class CharacterRarity(Flag):
    N = 1
    R = 2
    RPlus = 4
    SR = 8
    SRPlus = 16
    SSR = 32
    SSRPlus = 64
    UR = 128
    URPlus = 256
    LR = 512
    LRPlus1 = 1024
    LRPlus2 = 2048
    LRPlus3 = 4096
    LRPlus4 = 8192
    LRPlus5 = 16384
    LRPlus6 = 32768
    LRPlus7 = 65536
    LRPlus8 = 131072
    LRPlus9 = 262144
    LRPlus10 = 524288

class BaseParameter(_Enum):
    STR = (1, '[BaseParameterTypeMuscle]')
    DEX = (2, '[BaseParameterTypeEnergy]')
    MAG = (3, '[BaseParameterTypeIntelligence]')
    STA = (4, '[BaseParameterTypeHealth]')

class BattleParameter(_Enum):
    HP = (1, '[BattleParameterTypeHp]')
    ATK = (2, '[BattleParameterTypeAttackPower]')
    P_DEF = (3, '[BattleParameterTypePhysicalDamageRelax]')
    M_DEF = (4, '[BattleParameterTypeMagicDamageRelax]')
    ACC = (5, '[BattleParameterTypeHit]')
    EVD = (6, '[BattleParameterTypeAvoidance]')
    CRIT = (7, '[BattleParameterTypeCritical]')
    CRIT_RES = (8, '[BattleParameterTypeCriticalResist]')
    CRIT_DMG_BOOST = (9, '[BattleParameterTypeCriticalDamageEnhance]')
    P_CRIT_DMG_CUT = (10, '[BattleParameterTypePhysicalCriticalDamageRelax]')
    M_CRIT_DMG_CUT = (11, '[BattleParameterTypeMagicCriticalDamageRelax]')
    DEF_BREAK = (12, '[BattleParameterTypeDefensePenetration]')
    DEF = (13, '[BattleParameterTypeDefense]')
    PM_DEF_BREAK = (14, '[BattleParameterTypeDamageEnhance]')
    DEBUFF_ACC = (15, '[BattleParameterTypeDebuffHit]')
    DEBUFF_RES = (16, '[BattleParameterTypeDebuffResist]')
    COUNTER = (17, '[BattleParameterTypeDamageReflect]')
    HP_DRAIN = (18, '[BattleParameterTypeHpDrain]')
    SPD = (19, '[BattleParameterTypeSpeed]')



    