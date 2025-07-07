from enum import Enum, StrEnum, IntEnum, IntFlag

# General
class Server(IntEnum):
    Japan = 1
    Korea = 2
    Asia = 3
    America = 4
    Europe = 5
    Global = 6

class Language(StrEnum):
    jajp = 'jajp'
    kokr = 'kokr'
    enus = 'enus'
    zhtw = 'zhtw'
    dede = 'dede'
    esmx = 'esmx'
    frfr = 'frfr'
    idid = 'idid'
    ptbr = 'ptbr'
    ruru = 'ruru'
    thth = 'thth'
    vivn = 'vivn'
    zhcn = 'zhcn'

class Element(IntEnum):
    Azure = 1
    Crimson = 2
    Emerald = 3
    Amber = 4
    Radiance = 5
    Chaos = 6

class BaseParameter(IntEnum):
    STR = 1
    DEX = 2
    MAG = 3
    STA = 4

class BattleParameter(IntEnum):
    HP = 1
    ATK = 2
    P_DEF = 3
    M_DEF = 4
    ACC = 5
    EVD = 6
    CRIT = 7
    CRIT_RES = 8
    CRIT_DMG_BOOST = 9
    P_CRIT_DMG_CUT = 10
    M_CRIT_DMG_CUT = 11
    DEF_BREAK = 12
    DEF = 13
    PM_DEF_BREAK = 14
    DEBUFF_ACC = 15
    DEBUFF_RES = 16
    COUNTER = 17
    HP_DRAIN = 18
    SPD = 19

# Character
class Job(IntFlag):
    Warrior = 1
    Sniper = 2
    Sorcerer = 4

class CharacterRarity(IntFlag):
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

class BloodType(Enum):
    Unknown = 0   # Liz, Matilda
    A = 1
    B = 2
    O = 3
    AB = 4

class VoiceCategory(Enum):
    Basic = 0
    Birthday = 1
    ComeBack = 2
    Login = 3
    RankUp = 4
    Other = 5
    Appear = 6
    SignaturePhrase = 7
    BattleWin = 8
    BattleLose = 9
    Monologue = 10

class VoiceUnlock(Enum):
    None_ = 0
    RankUp1 = 1
    RankUp2 = 2
    RankUp3 = 3
    RankUp4 = 4
    RankUp5 = 5
    RankUp6 = 6
    Birthday = 7
    MemoryComplete = 8
    QuestClear = 9

# PvE
class UnitIconType(IntEnum):
    Character = 0
    EnemyCharacter = 1
    WitchQlipha = 2

# Not same as UnitType enum
# For enemy ID in MB
class EnemyType(IntEnum):
    AutoBattle = 1
    BossBattle = 2
    Tower = 3
    Temple = 4  # Now unused
    # Cave = 5 ?
    GuildTower = 6

class TowerType(IntEnum):
    Infinity = 1
    Azure = 2
    Crimson = 3
    Emerald = 4
    Amber = 5

# Equipment
class EquipSlot(IntEnum):
    Weapon = 1
    Sub = 2
    Gauntlet= 3
    Helmet = 4
    Armor = 5
    Shoes = 6
    
# Items
class ItemRarity(IntFlag):
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

class ItemType(IntEnum):
    # None_ = 0
    CurrencyFree = 1
    CurrencyPaid = 2
    Gold = 3
    Equipment = 4
    EquipmentFragment = 5
    Character = 6
    CharacterFragment = 7
    DungeonBattleRelic = 8
    EquipmentSetMaterial = 9
    QuestQuickTicket = 10
    CharacterTrainingMaterial = 11
    EquipmentReinforcementItem = 12
    ExchangePlaceItem = 13
    Sphere = 14
    MatchlessSacredTreasureExpItem = 15
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

class RuneType(IntEnum):
    STR = 1
    DEX = 2
    MAG = 3
    ATK = 4
    PM_DEF_BREAK = 5
    ACC = 6
    CRIT = 7
    DEBUFF_ACC = 8
    SPD = 9
    STA = 10
    HP = 11
    P_DEF = 12
    M_DEF = 13
    EVD = 14
    CRIT_RES = 15
    DEBUFF_RES = 16

# Skills
class NormalSkill(IntEnum):
    Physical = 101
    Magical = 102

class PassiveTrigger(IntEnum):
    None_ = 0
    TurnStart = 1
    TurnEnd = 2
    BeforeCalculation = 3
    InstantDeathDamage = 5
    SelfDead = 6
    AllyDead = 7
    ReceiveDamage = 8
    GiveDamage = 9
    AllyReceiveDamage = 10
    ReceiveDebuff = 11
    GiveDeBuff = 12
    AllyReceiveDeBuff = 13
    GiveHeal = 14
    AllyReceiveHeal = 15
    GiveBuff = 16
    AllyGiveBuff = 17
    EnemyRecovery = 18
    SelfRecovery = 19
    OtherEnemyDead = 20
    EnemyDead = 21
    AllyGiveDamage = 22
    EnemyReceiveHeal = 23
    ReceiveBuff = 24
    EnemyGiveBuff = 25
    BattleStart = 26
    BattleEnd = 27
    TurnStartBeforeSpeedCheck = 28
    TargetAttack = 29
    ReceiveHeal = 30
    ReceiveResonanceDamage = 31
    ActionStart = 32
    ActionEnd = 33
    SelfInjury = 34
    AllySelfInjury = 35
    ReceiveConfuseActionDebuff = 36
    GiveConfuseActionDebuff = 37
    AllyReceiveConfuseActionDebuff = 38
    TurnStartBType = 39
    ReceiveRemoveBuff = 40
    CheckReceiveDamageSelf = 41
    CheckReceiveDamage = 42
    NextCheckReceiveDamageSelf = 43
    NextCheckReceiveDamage = 44
    AlwaysEnemyDead = 45
    RecoveryFromInstantDeathDamage = 52
    SpecialDamageDead = 62
    MissingData = -1

    @classmethod  # In case new trigger is added
    def _missing_(cls, value):
        return cls.MissingData

# Gacha SelectListType
class GachaType(IntEnum):
    Fleeting = 1
    IoC = 2
    IoSG = 3
    Chosen = 4
