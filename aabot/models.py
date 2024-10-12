from dataclasses import dataclass
from enum import Enum
from typing import List


class GachaSelectListType(Enum):
    # [Description("なし")]
    None_ = 0
    # [Description("プライズ共通")]
    Default = 1
    # [Description("運命")]
    Destiny = 2
    # [Description("星の導き")]
    StarsGuidance = 3
    # [Description("選択ピックアップ")]
    SelectablePickUp = 4


# ------------------------------------
@dataclass
class Base():
    id: int

    def raw(self) -> dict:
        '''Returns data as is'''
        return self.__dict__

    def nice(self) -> dict:
        '''Returns data with enums converted to strings'''
        raise NotImplementedError()

@dataclass
class Character(Base):
    name: str
    title: str
    element: int
    base_rarity: int
    job: int
    speed: int
    uw_id: int
    actives: List[int]
    passives: List[int]


'''
class GachaCategoryType(_Enum):
    # [Description("キャラ")]
    Character = 0
    # [Description("武具")]
    Equipment = 1

# [Description("運命ガチャタイプ")]
class GachaDestinyType(_Enum):
    # [Description("なし")]
    None_ = 0
    # [Description("愁、業、心、渇属性")]
    BlueAndRedAndGreenAndYellow = 1
    # [Description("こちらの承認")]
    LightAndDark = 2

# [Description("ガチャグループタイプ")]
class GachaGroupType(_Enum):
    # [Description("グループ無し")]
    None_ = 0
    # [Description("属性")]
    Element = 1
    # [Description("聖天使の神託")]
    HolyAngel = 2

# [Description("ガチャ聖遺物タイプ")]
class GachaRelicType(_Enum):
    None_ = 0
    # [Description("天契の聖杯")]
    ChaliceOfHeavenly = 1
    # [Description("蒼穹の銀勲")]
    SilverOrderOfTheBlueSky = 2
    # [Description("希求の神翼")]
    DivineWingsOfDesire = 3
    # [Description("悠園の果実")]
    FruitOfTheGarden = 4

# [Description("ガチャリセットタイプ")]
class GachaResetType(_Enum):
    # [Description("リセット無し")]
    None_ = 0
    # [Description("毎日4:00")]
    Daily = 1
    # [Description("毎週月曜4:00")]
    Weekly = 2

# [Description("ガチャセレクトリストタイプ")]
class GachaSelectListType(Enum):
    # [Description("なし")]
    None_ = 0
    # [Description("プライズ共通")]
    Default = 1
    # [Description("運命")]
    Destiny = 2
    # [Description("星の導き")]
    StarsGuidance = 3
    # [Description("選択ピックアップ")]
    SelectablePickUp = 4

# [Description("ガチャ表示用フラグ")]
# [Flags]
class GachaCaseFlags(_Enum):
    # [Description("なし")]
    None_ = 0
    # [Description("天井表示")]
    ShowCeilingCount = 1
    # [Description("レビュー誘導判定無し")]
    IgnoreReview = 2
    # [Description("シェアボタン表示なし")]
    HideShareButton = 4
    # [Description("ガチャ詳細ダイアログ スペシャルリスト非表示")]
    HideSpecialList = 8
'''
@dataclass
class GachaPickup(Base):
    id: int
    start: int
    end: int
    select_list_type: int
    char_id: int
    
    def nice(self):
        nice = self.__dict__.copy()
        nice['select_list_type'] = GachaSelectListType(self.select_list_type).name

        return nice

    def is_active(self):
        raise NotImplementedError


    