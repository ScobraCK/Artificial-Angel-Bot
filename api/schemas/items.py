from api.schemas import requests
from api.utils.masterdata import MasterData
from api.utils.error import APIError
from common import enums, schemas

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

async def get_rune(md: MasterData, payload: requests.RuneRequest):
    try:
        rune_data = next(await md.search_filter(CategoryId=payload.category.value, Lv=payload.level))  # RuneType is _Enum not IntEnum
        return schemas.Rune(rune_data)
    except StopIteration:
        raise APIError('Rune could not be found')

async def get_item(md: MasterData, payload: requests.ItemRequest) -> schemas.ItemBase:
    try:
        if (item_type := payload.item_type) == enums.ItemType.EquipmentFragment:
            equip_frag_data = await md.search_id(payload.item_id, 'EquipmentCompositeMB')
            equip_data = await md.search_id(equip_frag_data['EquipmentId'], 'EquipmentMB')
            item = schemas.EquipmentFragment(**equip_frag_data, icon=equip_data['IconId'], equip_name=equip_data['NameKey'])
        elif item_type == enums.ItemType.Character:  
            char_data = await md.search_id(payload.item_id, 'CharacterMB')
            item = schemas.CharacterItem(**char_data)
        elif item_type == enums.ItemType.CharacterFragment:
            char_data = await md.search_id(payload.item_id, 'CharacterMB')
            item = schemas.CharacterFragment(**char_data)
        elif item_type == enums.ItemType.EquipmentSetMaterial:
            equip_setm_data = await md.search_id(payload.item_id, 'EquipmentSetMaterialMB')
            item = schemas.EquipmentSetMaterial(**equip_setm_data)
        elif item_type == enums.ItemType.Sphere:  # Rune
            rune_data = await md.search_id(payload.item_id, 'SphereMB')
            item = schemas.Rune(**rune_data)
        elif item_type == enums.ItemType.TreasureChest:
            treasure_data = await md.search_id(payload.item_id, 'TreasureChestMB')
            item = schemas.TreasureChest(**treasure_data, ItemId=payload.item_id, ItemType=item_type)
        else:
            item_data = next(await md.search_filter('ItemMB', ItemId=payload.item_id, ItemType=payload.item_type))
            item = schemas.ItemBase(**item_data)
        return item
    except TypeError:  # None result from search_id
        raise APIError('Item could not be found.')
    except StopIteration:  # Not found
        raise APIError('Item could not be found or given item type is not supported.')

async def get_runes(md: MasterData, category: enums.RuneType|None = None) -> list[schemas.Rune]:
    if category is None:
        rune_data = await md.search_filter('SphereMB')
    else:
        if not isinstance(category, enums.RuneType):
            raise APIError(f'Invalid rune category: {category}')
        rune_data = await md.search_filter('SphereMB', CategoryId=category)
    return [schemas.Rune(**data) for data in rune_data]

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