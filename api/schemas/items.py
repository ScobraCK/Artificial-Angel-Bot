from fastapi import Query
from pydantic import (
    BaseModel, Field, AliasChoices,
    FieldSerializationInfo, field_serializer,
    ValidationInfo, field_validator, model_validator,
    )
from typing import List, Optional, Literal, Union

import api.schemas.parameters as params
import api.schemas.serializers as serializers
import api.utils.enums as enums
from api.utils.masterdata import MasterData
from api.utils.error import APIError


class _ItemBase(BaseModel):
    id: int = Field(..., validation_alias='Id')
    item_id: int = Field(..., validation_alias='ItemId')
    item_type: enums.ItemType = Field(..., validation_alias='ItemType')
    name: str = Field(..., validation_alias='NameKey')
    description: str = Field(..., validation_alias='DescriptionKey')
    icon: int = Field(..., validation_alias='IconId')
    rarity: enums.ItemRarity = Field(..., validation_alias=AliasChoices('ItemRarityFlags', 'RarityFlags'))
    max_count: int = Field(0, validation_alias='MaxItemCount')

    _serialize_str = field_serializer(
        'name', 'description',
        )(serializers.serialize_str)
    
    _serialize_enum = field_serializer(
        'rarity',
        )(serializers.serialize_enum)

class ItemBase(BaseModel):
    id: int = Field(...)
    item_id: int = Field(...)
    item_type: str = Field(...)
    name: str = Field(...)
    description: str = Field(...)
    icon: int = Field(...)
    rarity: Optional[str] = Field(...)  # Rarity may be 0 (None)
    max_count: int = Field(0)

class _Rune(_ItemBase):
    item_id: int = Field(..., validation_alias='Id')
    item_type: enums.ItemType = enums.ItemType.Sphere
    base_parameter: Optional[params._BaseParameterModel] = Field(...,validation_alias='BaseParameterChangeInfo')
    battle_parameter: Optional[params._BattleParameterModel] = Field(...,validation_alias='BattleParameterChangeInfo')
    category: enums.RuneType = Field(..., validation_alias='CategoryId')
    level: int = Field(..., validation_alias='Lv')
    sphere_type: int = Field(
        ..., ge=0, le=3,
        exclude=True,
        validation_alias='SphereType'
    )
    icon: Optional[int] = None  # added later, icon = {Category:02}{SphereType:02}

    @model_validator(mode='after')
    def add_icon(self):
        self.icon = int(f'{self.category.value:02}{self.sphere_type:02}')

        return self
    
class Rune(ItemBase):
    '''Item type 14, runes'''
    parameter: Union[params.BaseParameterModel, params.BattleParameterModel] = Field(
        ..., validation_alias=AliasChoices('base_parameter', 'battle_parameter')
    )
    category: str = Field(...)
    level: int = Field(...)

'''
# [Description("宝箱抽選タイプ")]
class TreasureChestLotteryType(_Enum):
    # [Description("抽選で1つ")]
    Random = 0
    # [Description("固定で1つ")]
    Static = 1
    # [Description("キャラクター1つを選択")]
    SelectCharacter = 2
    # [Description("アイテム1つを選択")]
    SelectItem = 3
    # [Description("選択した中から抽選")]
    SelectRandom = 4
    # [Description("複数の固定アイテム")]
    Fix = 5
    # [Description("抽選アイテムと固定アイテム")]
    RandomFix = 6
'''
# TODO
class _TreasureChest(_ItemBase):
    bulk_enabled: bool = Field(..., validation_alias='BulkUseEnabled')
    min_open_count: int = Field(..., validation_alias='MinOpenCount')
    lottery_type: int = Field(..., validation_alias='TreasureChestLotteryType')

Item = Union[Rune, ItemBase]

# Used to show an amount of item. Cost, reward etc
class ItemCount(BaseModel):
    item_id: int = Field(..., validation_alias='ItemId', examples=[1])
    item_type: int = Field(..., validation_alias='ItemType', examples=[3])
    count: int = Field(..., validation_alias='ItemCount', examples=[1000])

    class Config:
        populate_by_name = True
        
# Request
class ItemRequest(BaseModel):
    item_id: int = Field(Query())
    item_type: enums.ItemType = Field(Query())

class RuneRequest(BaseModel):
    category: enums.RuneType = Field(..., description='Rune type')
    level: int = Field(..., description='Rune level')

async def get_rune(md: MasterData, payload: RuneRequest):
    try:
        rune_data = next(await md.search_filter(CategoryId=payload.category.value, Lv=payload.level))  # RuneType is _Enum not IntEnum
        return _Rune(rune_data)
    except StopIteration:
        raise APIError('Rune could not be found')

async def get_item(md: MasterData, payload: ItemRequest) -> _ItemBase:
    if (item_type := payload.item_type) == enums.ItemType.Sphere:  # Rune
        rune_data = await md.search_id(payload.item_id, 'SphereMB')
        item = _Rune(**rune_data)
    elif item_type == enums.ItemType.TreasureChest:
        treasure_data = await md.search_id(payload.item_id, 'TreasureChestMB')
        item = _ItemBase(**treasure_data, ItemId=payload.item_id, ItemType=item_type)  # TODO finish treasure class
    else:
        try:
            item_data = next(await md.search_filter('ItemMB', ItemId=payload.item_id, ItemType=payload.item_type))
            item = _ItemBase(**item_data)
        except StopIteration:
            item = None
    
    if not item:
        raise APIError('Item could not be found (WIP: some items are missing).')
    
    return item

'''
using MementoMori.Ortega.Common.Utils;
using MementoMori.Ortega.Share;
using MementoMori.Ortega.Share.Data.DtoInfo;
using MementoMori.Ortega.Share.Data.Item;
using MementoMori.Ortega.Share.Enums;
using MementoMori.Ortega.Share.Master.Data;

namespace MementoMori.WebUI.Extensions;

public static class UserItemExtensions
{
    public class EquipmentInfo
    {
        public long Count { get; set; }
        public EquipmentMB EquipmentMb { get; set; }
        public string Name { get; set; }
        public UserEquipmentDtoInfo Info { get; set; }
    }

    public static EquipmentInfo ToEquipmentInfo(this IUserItem userItem)
    {
        var equipmentMb = Masters.EquipmentTable.GetById(userItem.ItemId);
        return new EquipmentInfo
        {
            Count = userItem.ItemCount,
            EquipmentMb = equipmentMb,
            Name = Masters.TextResourceTable.Get(equipmentMb.NameKey)
        };
    }

    public static EquipmentInfo ToEquipmentInfo(this UserEquipmentDtoInfo userItem)
    {
        var equipmentMb = Masters.EquipmentTable.GetById(userItem.EquipmentId);
        return new EquipmentInfo
        {
            Count = 1,
            EquipmentMb = equipmentMb,
            Name = Masters.TextResourceTable.Get(equipmentMb.NameKey),
            Info = userItem
        };
    }

    public class UserItemInfo
    {
        public string Name { get; set; }
        public string Description { get; set; }
        public long Count { get; set; }
        public ItemRarityFlags ItemRarityFlags { get; set; }
        public long MaxItemCount { get; set; }
        public IUserItem Item { get; set; }
    }

    public static UserItemInfo ToUserItemInfo(this IUserItem userItem)
    {
        if (userItem.ItemType == ItemType.TreasureChest)
        {
            var treasureChestMb = Masters.TreasureChestTable.GetById(userItem.ItemId);
            return new UserItemInfo
            {
                Name = Masters.TextResourceTable.Get(treasureChestMb.NameKey),
                Description = Masters.TextResourceTable.Get(treasureChestMb.DescriptionKey),
                Count = userItem.ItemCount,
                ItemRarityFlags = treasureChestMb.ItemRarityFlags,
                MaxItemCount = treasureChestMb.MaxItemCount,
                Item = userItem
            };
        }
        else if (userItem.ItemType == ItemType.CharacterFragment)
        {
            var characterMb = Masters.CharacterTable.GetById(userItem.ItemId);
            var characterName = Masters.TextResourceTable.Get(characterMb.NameKey);
            return new UserItemInfo()
            {
                Name = Masters.TextResourceTable.Get("[CommonItemCharacterFragment]", characterName),
                Description = Masters.TextResourceTable.Get("[ItemTypeCharacterFragmentDescription]", characterName, 60),
                Count = userItem.ItemCount,
                ItemRarityFlags = characterMb.ItemRarityFlags,
                MaxItemCount = 0,
                Item = userItem
            };
        }
        else if (userItem.ItemType == ItemType.EquipmentSetMaterial)
        {
            var equipmentSetMaterialMb = Masters.EquipmentSetMaterialTable.GetById(userItem.ItemId);
            var name = $"{Masters.TextResourceTable.Get(equipmentSetMaterialMb.NameKey)} Lv{equipmentSetMaterialMb.Lv}";
            return new UserItemInfo()
            {
                Name = name,
                Description = Masters.TextResourceTable.Get(equipmentSetMaterialMb.DescriptionKey),
                Count = userItem.ItemCount,
                ItemRarityFlags = equipmentSetMaterialMb.ItemRarityFlags,
                MaxItemCount = 0,
                Item = userItem
            };
        }
        else if (userItem.ItemType == ItemType.EquipmentFragment)
        {
            var equipmentCompositeMb = Masters.EquipmentCompositeTable.GetById(userItem.ItemId);
            var equipmentMb = Masters.EquipmentTable.GetById(equipmentCompositeMb.EquipmentId);
            var equipmentName = Masters.TextResourceTable.Get(equipmentMb.NameKey);
            return new UserItemInfo()
            {
                Name = Masters.TextResourceTable.Get("[CommonItemEquipmentFragmentFormat]", equipmentName),
                Description = Masters.TextResourceTable.Get("[ItemTypeEquipmentFragmentDescription]", equipmentName, equipmentCompositeMb!.RequiredFragmentCount),
                Count = userItem.ItemCount,
                ItemRarityFlags = (ItemRarityFlags) equipmentMb.RarityFlags,
                MaxItemCount = 0,
                Item = userItem
            };
        }
        else
        {
            var itemMb = Masters.ItemTable.GetByItemTypeAndItemId(userItem.ItemType, userItem.ItemId);
            return new UserItemInfo
            {
                Name = Masters.TextResourceTable.Get(itemMb.NameKey),
                Description = Masters.TextResourceTable.Get(itemMb.DescriptionKey),
                Count = userItem.ItemCount,
                ItemRarityFlags = itemMb.ItemRarityFlags,
                MaxItemCount = itemMb.MaxItemCount,
                Item = userItem
            };
        }
    }

    public class SphereInfo
    {
        public string Name { get; set; }
        public string Description { get; set; }
        public long Count { get; set; }
        public SphereMB SphereMB { get; set; }
        public long MaxItemCount { get; set; }
    }

    public static SphereInfo ToSphereInfo(this IUserItem userItem)
    {
        var sphereMb = Masters.SphereTable.GetById(userItem.ItemId);
        return new SphereInfo
        {
            Name = Masters.TextResourceTable.Get(sphereMb.NameKey),
            Description = Masters.TextResourceTable.Get(sphereMb.DescriptionKey),
            Count = userItem.ItemCount,
            SphereMB = sphereMb,
            MaxItemCount = 0
        };
    }


    public static string GetItemName(this IUserItem item)
    {
        if (item.ItemType == ItemType.Equipment)
        {
            var equipmentMb = Masters.EquipmentTable.GetById(item.ItemId);
            return $"{Masters.TextResourceTable.Get(equipmentMb.NameKey)} Lv{equipmentMb.EquipmentLv}";
        }
        if (item.ItemType == ItemType.TreasureChest)
        {
            var treasureChestMb = Masters.TreasureChestTable.GetById(item.ItemId);
            return Masters.TextResourceTable.Get(treasureChestMb.NameKey);
        }

        if (item.ItemType == ItemType.CharacterFragment)
        {
            var characterMb = Masters.CharacterTable.GetById(item.ItemId);
            var characterName = Masters.TextResourceTable.Get(characterMb.NameKey);
            return Masters.TextResourceTable.Get("[CommonItemCharacterFragment]", characterName);
        }

        if (item.ItemType == ItemType.EquipmentFragment)
        {
            var equipmentMb = Masters.EquipmentTable.GetById(item.ItemId);
            var equipmentName = $"{Masters.TextResourceTable.Get(equipmentMb.NameKey)} Lv{equipmentMb.EquipmentLv}";
            return Masters.TextResourceTable.Get("[CommonItemEquipmentFragmentFormat]", equipmentName);
        }

        if (item.ItemType == ItemType.EquipmentSetMaterial)
        {
            var equipmentSetMaterialMb = Masters.EquipmentSetMaterialTable.GetById(item.ItemId);
            var name = $"{Masters.TextResourceTable.Get(equipmentSetMaterialMb.NameKey)} Lv{equipmentSetMaterialMb.Lv}";
            return name;
        }

        if (item.ItemType == ItemType.Sphere)
        {
            var sphereMb = Masters.SphereTable.GetById(item.ItemId);
            return $"{Masters.TextResourceTable.Get(sphereMb.NameKey)} Lv{sphereMb.Lv}";
        }

        if (item.ItemType == ItemType.Character)
        {
            var characterMb = Masters.CharacterTable.GetById(item.ItemId);
            return Masters.TextResourceTable.Get(characterMb.NameKey);
        }

        var itemMb = Masters.ItemTable.GetByItemTypeAndItemId(item.ItemType, item.ItemId);
        return Masters.TextResourceTable.Get(itemMb.NameKey);
    }
}
'''

'''
class ItemType(_Enum):
    # [Description("なし")]
    None_ = 0
    # [Description("無償仮想通貨")]
    CurrencyFree = 1
    # [Description("有償仮想通貨")]
    CurrencyPaid = 2
    # [Description("ゲーム内通貨")]
    Gold = 3
    # [Description("武具")]
    Equipment = 4
    # [Description("武具の欠片")]
    EquipmentFragment = 5
    # [Description("キャラクター")]
    Character = 6
    # [Description("キャラクターの絆")]
    CharacterFragment = 7
    # [Description("洞窟の加護")]
    DungeonBattleRelic = 8
    # [Description("アダマンタイト")]
    EquipmentSetMaterial = 9
    # [Description("n時間分アイテム")]
    QuestQuickTicket = 10
    # [Description("キャラ育成素材")]
    CharacterTrainingMaterial = 11
    # [Description("武具強化アイテム")]
    EquipmentReinforcementItem = 12
    # [Description("交換所アイテム")]
    ExchangePlaceItem = 13
    # [Description("スフィア")]
    Sphere = 14
    # [Description("魔装強化アイテム")]
    MatchlessSacredTreasureExpItem = 15
    # [Description("ガチャチケット")]
    GachaTicket = 16
    # [Description("宝箱、未鑑定スフィアなど")]
    TreasureChest = 17
    # [Description("宝箱の鍵")]
    TreasureChestKey = 18
    # [Description("ボスチケット")]
    BossChallengeTicket = 19
    # [Description("無窮の塔チケット")]
    TowerBattleTicket = 20
    # [Description("回復の果実")]
    DungeonRecoveryItem = 21
    # [Description("プレイヤー経験値")]
    PlayerExp = 22
    # [Description("フレンドポイント")]
    FriendPoint = 23
    # [Description("生命樹の雫")]
    EquipmentRarityCrystal = 24
    # [Description("レベルリンク経験値")]
    LevelLinkExp = 25
    # [Description("ギルドストック")]
    GuildFame = 26
    # [Description("ギルド経験値")]
    GuildExp = 27
    # [Description("貢献メダル")]
    ActivityMedal = 28
    # [Description("VIP経験値")]
    VipExp = 29
    # [Description("パネル図鑑解放判定アイテム")]
    PanelGetJudgmentItem = 30
    # [Description("パネルミッション マス解放アイテム")]
    UnlockPanelGridItem = 31
    # [Description("パネル図鑑解放アイテム")]
    PanelUnlockItem = 32
    # [Description("楽曲チケット")]
    MusicTicket = 33
    # [Description("特別プレイヤーアイコン")]
    SpecialIcon = 34
    # [Description("アイコンの断片")]
    IconFragment = 35
    # [Description("タイプ強化アイテム")]
    GuildTowerJobReinforcementMaterial = 36
    # [Description("リアル景品(グッズ)")]
    RealPrizeGoods = 37
    # [Description("リアル景品(デジタル)")]
    RealPrizeDigital = 38
    # [Description("人気投票(ItemId => PopularityVoteMBのId)")]
    PopularityVote = 39
    # [Description("ラッキーチャンスガチャチケット")]
    LuckyChanceGachaTicket = 40
    # [Description("チャットふきだし")]
    ChatBalloon = 41
    # [Description("イベント交換所アイテム")]
    EventExchangePlaceItem = 50
    # [Description("Stripeクーポン")]
    StripeCoupon = 1001
'''