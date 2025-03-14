from io import StringIO
from collections import namedtuple, defaultdict
from discord import Color, Interaction, Embed
from re import finditer
from typing import Tuple, List, Union

from aabot.api import api
from aabot.api import response as resp
from aabot.db.database import SessionAABot
from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.skills import uw_skill_description
from aabot.pagination.views import DropdownView, MixedView
from aabot.utils import enums, emoji
from aabot.utils.alias import alias_lookup
from aabot.utils.error import BotError
from aabot.utils.utils import param_string

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

rarity_color = {
    'D': Color.default(),
    'C': Color.default(),
    'B': Color.default(),
    'A': Color.default(),
    'S': Color.default(),
    'R': Color.from_str('#aeb5bf'),
    'SR': Color.from_str('#d9af5b'),
    'SSR': Color.from_str('#8d54ab'),
    'UR': Color.from_str('#c0474e'),
    'LR': Color.from_str('#272c26'),
}

equip_type_string = {
    'sword': enums.EquipType.Sword,
    'gun': enums.EquipType.Gun,
    'pistol': enums.EquipType.Gun,
    'tome': enums.EquipType.Tome,
    'sub': enums.EquipType.Accessory,
    'accessory': enums.EquipType.Accessory,
    'necklace': enums.EquipType.Accessory,
    'ring': enums.EquipType.Accessory,
    'glove': enums.EquipType.Gauntlet,
    'gloves': enums.EquipType.Gauntlet,
    'hand': enums.EquipType.Gauntlet,
    'hands': enums.EquipType.Gauntlet,
    'gauntlet': enums.EquipType.Gauntlet,
    'helmet': enums.EquipType.Helmet,
    'head': enums.EquipType.Helmet,
    'chest': enums.EquipType.Chest,
    'chestplate': enums.EquipType.Chest,
    'armor': enums.EquipType.Chest,
    'armour': enums.EquipType.Chest,
    'body': enums.EquipType.Chest,
    'boot': enums.EquipType.Boots,
    'boots': enums.EquipType.Boots,
    'feet': enums.EquipType.Boots,
    'shoe': enums.EquipType.Boots,
    'shoes': enums.EquipType.Boots,
}

EquipArgs = namedtuple("EquipArgs", ["rarity", "level", "upgrade"])

class ItemCounter:
    def __init__(self, blacklist = []):
        self.items = defaultdict(int)  # Stores (item_id, item_type) -> count
        self.blacklist = blacklist  # type blacklist

    def add_items(self, items: Union[resp.ItemCount, List[resp.ItemCount], "ItemCounter"]):
        if isinstance(items, resp.ItemCount):  # Single item
            self.items[(items.item_id, items.item_type)] += items.count
        elif isinstance(items, list):  # List of items
            for item in items:
                if not isinstance(item, resp.ItemCount):
                    raise TypeError("List must contain only ItemCount instances")
                self.items[(item.item_id, item.item_type)] += item.count
        elif isinstance(items, ItemCounter):  # Another ItemCounter
            for (item_id, item_type), count in items.items.items():
                self.items[(item_id, item_type)] += count
        else:
            raise TypeError("Expected ItemCount, List[ItemCount], or ItemCounter")

    def get_total(self) -> List[resp.ItemCount]:
        return [resp.ItemCount(item_id, item_type, count) for (item_id, item_type), count in self.items.items() if item_type not in self.blacklist]
    
    async def get_total_strings(self) -> List[str]:
        return [await item_count_string(item) for item in self.get_total()]

    def __bool__(self) -> bool:
        return bool(self.items)


def item_embed(item_data: resp.APIResponse[resp.Item]):
    item = item_data.data
    title = item.name
    description = (
        f'**Id:** {item.id}\n'
        f'**Item id:** {item.id}\n'
        f'**Item type:** {enums.ItemType(item.item_type).name}({item.item_type})\n'
        f'Max: {item.max_count if item.max_count else 'No limit'}\n\n'
        f'**Description**\n{item.description}\n\n'
    )
    
    if isinstance(item, resp.Rune):
        title = f'{title} Lv.{item.level}'
        description += (
            '**Details**\n'
            f'Type: {item.category}\n'
            f'Level: {item.level}\n'
            f'Parameter: {item.parameter}'
        )
    
    return BaseEmbed(
        item_data.version,
        title=title,
        description=description,
        color=rarity_color.get(item.rarity)
    )

async def item_count_string(itemcount: resp.ItemCount) -> str:
    # TODO emojis
    if itemcount.item_type == 5:
        return f'{itemcount.count:,}x Fragments'  # Temp solution
    if itemcount.item_type == 9:
        return f'{itemcount.count:,}x Temp'  # Temp solution
    item_data = await api.fetch_item(itemcount.item_id, itemcount.item_type)
    item = item_data.data
    return f'{itemcount.count:,}x {item.name}'

def parse_equip_string(string: str) -> Tuple[str|enums.EquipType, List[EquipArgs]]:
    tokens = string.split(maxsplit=1)
    if len(tokens) < 2:
        raise BotError(f'Equipment string `{string}` was incorrect. Use `/help equipment` for more info.')
    
    type_token, equip_token = tokens
    
    equip_type = equip_type_string.get(type_token.lower())
    if not equip_type:
        equip_type = type_token  # character
    
    pattern = r'(?P<rarity>[a-zA-Z]+)\s*(?P<level>\d+)?\s*(?P<upgrade>\+\d+)?(?=\s|$)'
    matches = finditer(pattern, equip_token)

    results = []
    for match in matches:
        rarity = match.group('rarity').upper()
        level=match.group("level")
        upgrade=match.group("upgrade")
        
        if rarity != 'SP' and (rarity not in enums.EquipRarity.__members__):  # SP is for S+
            raise BotError(f'Got undefined rarity `{rarity}`. Only D-A, S, SP(S+), SR, SSR, UR, LR allowed.')
        
        if upgrade:
            upgrade = int(upgrade.lstrip('+'))
        else:
            upgrade = 0
        
        if not level:
            if not upgrade:
                raise BotError('Level was not specified.')
            level = upgrade  # level and upgrade can be None
        else:
            level = int(level)
        
        results.append(
            EquipArgs(
                rarity=rarity,
                level=level,
                upgrade=upgrade
            )
        )
    
    if not results:
        raise BotError(f'Equipment string `{string}` was incorrect. Use `/help equipment` for more info.')

    return equip_type, results

async def get_equipment(equip_type: enums.EquipType|str, equipment_args: EquipArgs, language: enums.Language):
    rarity = equipment_args.rarity
    level = equipment_args.level
    upgrade = equipment_args.upgrade

    if rarity == 'SP':
        rarity = 'S'
        quality = 1
    else:
        quality = None
    
    if isinstance(equip_type, enums.EquipType):
        equipment_data = await api.fetch_api(
            api.EQUIPMENT_NORMAL_PATH,
            query_params={
                'slot': equip_type.value.slot,
                'job': equip_type.value.job,
                'rarity': enums.EquipRarity[rarity].value,
                'level': level,
                'quality': quality,
                'language': language
            },
            response_model=resp.Equipment
        )
    else:  # character string
        with SessionAABot() as session:
            char_id = alias_lookup(session, equip_type)
        equipment_data = await api.fetch_api(
            api.EQUIPMENT_UNIQUE_PATH,
            response_model=resp.UniqueWeapon,
            query_params= {
                'rarity': enums.EquipRarity[rarity].value,
                'level': level,   
                'character': char_id,
                'language': language
            },
        )
        
    equip_id = equipment_data.data.equip_id

    upgrade_data = await api.fetch_api(
        api.EQUIPMENT_UPGRADE_PATH,
        response_model=resp.EquipmentCosts,
        query_params={
            'equip_id': equip_id,
            'upgrade': upgrade,
            'language': language
        }
    )

    return equipment_data, upgrade_data

def equip_embed(equip_data: resp.APIResponse[resp.Equipment|resp.UniqueWeapon], upgrade=0, upgrade_coeff=1):
    equipment = equip_data.data
    description = StringIO()

    # Base Description
    description.write(
        f'Type: {equipment.slot}\n'
        f'Level: {equipment.level}\n'
        f'Upgrade: {upgrade}\n\n'
    )
    
    # Stats
    max_value = int(equipment.bonus_parameters * 0.6)
    sub_value = equipment.bonus_parameters - max_value
    mainstat = int(equipment.basestat.value * upgrade_coeff)
    description.write(
        f'**Stats**\n'
        f"```\n{equipment.basestat.type}: {mainstat:,} (Base: {equipment.basestat.value:,})\n"
        f"Bonus Parameters: {equipment.bonus_parameters:,}\n"
        f"Max: {max_value:,}\n"
        f"Sub: {sub_value:,}```\n"
    )

    # Set Bonus
    if equip_set := equipment.equipment_set:
        description.write(f'**{equip_set.name}**\n```\n')
        description.write(
            "\n".join(
                f"{effect.equipment_count} Pieces: {param_string(effect.parameter)}" 
                for effect in equip_set.set_effects
            )
        )
        description.write('```')

    # UW
    if isinstance(equip_data, resp.UniqueWeapon):
        description.write('**Unique Passive Effect**\n```\n')
        description.write('\n'.join(param_string(param) for param in equip_data.uw_bonus))

    return BaseEmbed(
        version=equip_data.version,
        title=f'{emoji.rarity_emoji.get(equipment.rarity)} {equipment.rarity} {equipment.name}',
        description=description.getvalue(),
        color=Color.blurple()
    )

def uw_embed(equipment_data: resp.APIResponse[resp.UniqueWeapon]):
    '''UW Descriptions Embed'''
    return BaseEmbed(
        equipment_data.version,
        title=f'{emoji.rarity_emoji.get(equipment_data.data.rarity)} {equipment_data.data.rarity} {equipment_data.data.name}',
        description=uw_skill_description(equipment_data.data.uw_descriptions),
        color=Color.blurple()
    )

async def cost_description(costs: resp.EquipmentCosts, start_level: int=0, start_upgrade: int=0, start_rarity: str=None):
    description = StringIO()
    total_items = ItemCounter(blacklist=[9])
    synth_items = ItemCounter()
    enhance_items = ItemCounter(blacklist=[9])
    upgrade_items = ItemCounter()
    
    description.write(
        f'**Base Equipment:** {f'{start_rarity} {start_level}+{start_upgrade}' if start_rarity else 'None'}\n'
        f'**Target Equipment:** {costs.equipment.rarity} {costs.equipment.level}+{costs.upgrade_costs.upgrades[-1].upgrade_level if costs.upgrade_costs.upgrades else 0}\n\n'
    )
    
    # Costs
    if costs.synthesis_costs and start_rarity is None:
        synth_items.add_items(costs.synthesis_costs.cost)
        current_rarity = costs.synthesis_costs.rarity
    else:
        current_rarity = start_rarity

    if costs.rarity_enhance_costs:
        for cost in costs.rarity_enhance_costs:
            if cost.before_rarity == current_rarity:
                current_rarity = cost.after_rarity
                enhance_items.add_items(cost.cost)
                
    if costs.equipment.rarity != current_rarity:  # should always end up as final upgrade
        raise BotError(f'Starting {start_rarity} {costs.equipment.slot} cannot be upgraded to {costs.equipment.rarity} {costs.equipment.slot}')

    for cost in costs.enhance_costs:
        if cost.before_level < start_level:
            continue
        enhance_items.add_items(cost.cost)
    
    for cost in costs.upgrade_costs.upgrades:
        if cost.upgrade_level < start_upgrade:  # always start at 1. Maybe change it to before/after.
            continue
        upgrade_items.add_items(cost.cost)
        
    # Descriptions
    if synth_items:
        description.write('**Synthesis Costs**\n')
        description.write(f'{'\n'.join(await synth_items.get_total_strings())}\n\n')
        total_items.add_items(synth_items)

    if enhance_items:
        description.write('**Enhance Costs**\n')
        description.write(f'{'\n'.join(await enhance_items.get_total_strings())}\n\n')
        total_items.add_items(enhance_items)

    if upgrade_items:
        description.write('**Upgrade Costs**\n')
        description.write(f'{'\n'.join(await upgrade_items.get_total_strings())}\n\n')
        total_items.add_items(upgrade_items)

    if total_items:
        description.write('**Total Costs**\n')
        description.write(f'{'\n'.join(await total_items.get_total_strings())}')
    else:
        description.write('No costs')
        
    return description.getvalue()

async def upgrade_embed(upgrade_data: resp.APIResponse[resp.EquipmentCosts], start_level=0, start_upgrade=0, start_rarity=None):
    costs = upgrade_data.data
    equipment = costs.equipment

    return BaseEmbed(
        upgrade_data.version,
        title = f'{emoji.rarity_emoji.get(equipment.rarity)} {equipment.rarity} {equipment.name}',
        description=await cost_description(costs, start_level, start_upgrade, start_rarity),
        color=Color.blurple()
    )
    
async def equipment_view(interaction: Interaction, equip_string: str, language: enums.Language):
    embed_dict = {}
    embed_dict['Equipment Details'] = []
    embed_dict['Costs'] = []
    equip_type, results = parse_equip_string(equip_string)
    
    if len(results) > 5:
        raise BotError('Too many equipment strings. Maximum of 5 allowed.')

    equipments: List[resp.APIResponse[resp.Equipment]]|List[resp.APIResponse[resp.UniqueWeapon]] = []
    upgrades: List[resp.APIResponse[resp.EquipmentCosts]] = []
    # Main embeds

    for eqp_args in results:
        if eqp_args.upgrade < results[0].upgrade:
            raise BotError(
                'Upgrade level cannot be lower than the first equipment. Was given:\n'
                f'{'\n'.join(f'{i}. `{equip.rarity} {equip.level}+{equip.upgrade}`' for i, equip in enumerate(results))}'
                )
        if eqp_args.level < results[0].level:
            raise BotError(
                'Equipment level cannot be lower than the first equipment. Was given:\n'
                f'{'\n'.join(f'{i}. `{equip.rarity} {equip.level}+{equip.upgrade}`' for i, equip in enumerate(results))}'
            )
        if enums.EquipRarity[eqp_args.rarity].value < enums.EquipRarity[results[0].rarity].value:
            raise BotError(
                'Equipment rarity cannot be lower than the first equipment. Was given:\n'
                f'{'\n'.join(f'{i}. `{equip.rarity} {equip.level}+{equip.upgrade}`' for i, equip in enumerate(results))}'
            )
        equipment_data, upgrade_data = await get_equipment(equip_type, eqp_args, language)
        equipments.append(equipment_data)
        upgrades.append(upgrade_data)
    
    for equipment_data, upgrade_data in zip(equipments, upgrades):
        if upgrade_costs := upgrade_data.data.upgrade_costs.upgrades:  # upgrade > 0
            upgrade_level = upgrade_costs[-1].upgrade_level
            coefficient = upgrade_costs[-1].coefficient
            embed_dict['Equipment Details'].append(equip_embed(equipment_data, upgrade_level, coefficient))
        else:
            embed_dict['Equipment Details'].append(equip_embed(equipment_data))

    if len(equipments) == 1:
        embed_dict['Costs'].append(await upgrade_embed(upgrade_data))
    else:
        for upgrade_data in upgrades[1:]:
            embed_dict['Costs'].append(await upgrade_embed(upgrade_data, results[0].level, results[0].upgrade, results[0].rarity))
    
    # UW descriptions
    if isinstance(equipments[0].data, resp.UniqueWeapon):
        embed_dict['UW Skills'] = [uw_embed(equipments[0])]

    return MixedView(interaction.user, embed_dict, 'Equipment Details')


def equipment_help_description():
    text = StringIO()
    text.write(
        "## Equipment Help\n"
        "**String Parameters**\n"
        'Equipment String: `[Equipment Type] [Equipment Details 1] [Equipment Details 2]...`\n\n'
        "**Equipment Type:**\n"
        "Character Name or Equipment Type."
        f"Tries to search for equipment type in `{', '.join(equip_type_string.keys())}`.\n"
        "If not found, will search for a Unique Weapon with that character name match.\n\n"
        
        '**Equipment Details**\n'
        "Provides details for equipment rarity, level, and upgrade level. Can add up to 5 equipment details to compare.\n"
        "**Rarity:** D, C, B, A, S, SP(S+), R, SR, SSR, UR, LR. Lowercase is allowed.\n\n"
        "**Level:** integer for the gear level. If the level doesn't exist will return error.\n\n"
        "**Upgrade Level:** Upgrade Level of gear. Integer after '+' prefix (Ex: +120). Will default to 0 if not provided. Additionally it is possible to omit the equipment level and write only the upgrade level. This will assume the upgrade level is the same as the equipment level.\n\n"
        "```Examples: \n"
        "ssr240+120 -> Rarity: SSR Level: 240 Upgrade Level:120\n"
        "UR300 -> Rarity: UR Level: 300 Upgrade Level:0\n"
        "LR+240 -> Rarity: LR Level: 240 Upgrade Level:240```"
    )

    return text.getvalue()

    
        
    







        
    
    