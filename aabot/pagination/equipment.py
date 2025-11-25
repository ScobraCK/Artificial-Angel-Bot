from collections import namedtuple
from enum import Enum
from io import StringIO
from re import finditer

from discord import Color, Interaction, ui
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import MixedView
from aabot.pagination.view import BaseContainer
from aabot.pagination.skills import get_uw_skill_text
from aabot.utils import api
from aabot.utils.alias import alias_lookup
from aabot.utils.assets import EQUIPMENT_THUMBNAIL
from aabot.utils.emoji import to_emoji
from aabot.utils.error import BotError, BotAPIError
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.utils import param_string, remove_linebreaks

from common import enums, schemas
from common.database import SessionAA


EquipTypeTuple = namedtuple('EquipTypeTuple', ['slot', 'job'])
EquipArgs = namedtuple("EquipArgs", ["rarity", "level", "upgrade"])

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

equip_type_string = {
    'sword': EquipType.Sword,
    'gun': EquipType.Gun,
    'pistol': EquipType.Gun,
    'tome': EquipType.Tome,
    'sub': EquipType.Accessory,
    'accessory': EquipType.Accessory,
    'necklace': EquipType.Accessory,
    'ring': EquipType.Accessory,
    'glove': EquipType.Gauntlet,
    'gloves': EquipType.Gauntlet,
    'hand': EquipType.Gauntlet,
    'hands': EquipType.Gauntlet,
    'gauntlet': EquipType.Gauntlet,
    'helmet': EquipType.Helmet,
    'head': EquipType.Helmet,
    'chest': EquipType.Chest,
    'chestplate': EquipType.Chest,
    'armor': EquipType.Chest,
    'armour': EquipType.Chest,
    'body': EquipType.Chest,
    'dress': EquipType.Chest,
    'boot': EquipType.Boots,
    'boots': EquipType.Boots,
    'feet': EquipType.Boots,
    'shoe': EquipType.Boots,
    'shoes': EquipType.Boots,
}


def parse_equip_string(string: str) -> tuple[str|EquipType, list[EquipArgs]]:
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
        rarity = match.group('rarity').upper()  # string rarity
        level=match.group("level")
        upgrade=match.group("upgrade")

        if rarity != 'SP' and (rarity not in enums.ItemRarity.__members__):  # SP is for S+
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

async def find_equipment(equip_type: EquipType|str, equipment_args: EquipArgs, language: enums.Language) -> schemas.APIResponse[schemas.Equipment|schemas.UniqueWeapon]:
    rarity = equipment_args.rarity
    level = equipment_args.level

    if rarity == 'SP':
        rarity = 'S'
        quality = 1
    else:
        quality = None

    if isinstance(equip_type, EquipType):
        equipment_resp = await api.fetch_api(
            api.EQUIPMENT_SEARCH_PATH,
            query_params={
                'slot': equip_type.value.slot,
                'job': equip_type.value.job,
                'rarity': enums.ItemRarity[rarity].value,  # string -> rarity flag
                'level': level,
                'quality': quality,
                'language': language
            },
            response_model=schemas.Equipment
        )
    else:  # character string
        async with SessionAA() as session:
            char_id = await alias_lookup(session, equip_type)
        equipment_resp = await api.fetch_api(
            api.EQUIPMENT_UW_SEARCH_PATH,
            response_model=schemas.UniqueWeapon,
            query_params= {
                'rarity': enums.ItemRarity[rarity].value,  # string -> rarity flag
                'level': level,
                'character': char_id,
                'language': language
            },
        )

    return equipment_resp

async def get_uw(char_id: int, language: enums.Language) -> schemas.APIResponse[schemas.UniqueWeapon]:
    '''Returns LR240 UW data'''
    try:
        uw_resp = await api.fetch_api(
            api.EQUIPMENT_UW_SEARCH_PATH,
            response_model=schemas.UniqueWeapon,
            query_params={
                'rarity': enums.ItemRarity.LR.value,
                'level': 240,
                'character': char_id,
                'language': language
            }
        )
        return uw_resp
    except BotAPIError as e:
        if e.status_code == 404:
            return None
        else:
            raise e
            

async def get_upgrade_costs(equip_id: int, upgrade: int, language: enums.Language) -> schemas.APIResponse[schemas.EquipmentCosts]:
    upgrade_resp = await api.fetch_api(
        api.EQUIPMENT_UPGRADE_PATH,
        response_model=schemas.EquipmentCosts,
        query_params={
            'equip_id': equip_id,
            'upgrade': upgrade,
            'language': language
        }
    )
    return upgrade_resp

async def equipment_detail_ui(equipment: schemas.Equipment|schemas.UniqueWeapon, cs: schemas.CommonStrings, upgrade=0, upgrade_coeff=1) -> BaseContainer:
    '''Equipment needs to be fetched outside of this function and version added afterwards.'''
    container = BaseContainer()

    async with SessionAA() as session:
        emoji_str = enums.EquipSlot(equipment.slot).name
        if equipment.slot == 1:  # weapon
            emoji_str = f'{emoji_str}_{equipment.job}'

        emoji = await to_emoji(session, emoji_str)

    title = f'{emoji} {enums.ItemRarity(equipment.rarity).name} {equipment.name} | Lv{equipment.level}'
    if upgrade:
        title += f'+{upgrade}'

    max_value = int(equipment.bonus_parameters * 0.6) + 2  # locking can cause +1/+2
    sub_value = equipment.bonus_parameters - max_value
    mainstat = int(equipment.basestat.value * upgrade_coeff)

    container.add_item(
        ui.Section(
            ui.TextDisplay(f'### {title}'),
            accessory=ui.Thumbnail(EQUIPMENT_THUMBNAIL.format(equip_id=equipment.icon_id))
        )
    ).add_item(
        ui.TextDisplay(
            f'**Stats**\n```\n'
            f"{cs.battle_param[equipment.basestat.type]}: {mainstat:,} (Base: {equipment.basestat.value:,})\n"
            f"Bonus Parameters: {equipment.bonus_parameters:,}\n"
            f"- Max: {max_value:,}\n"
            f"- Sub: {sub_value:,}\n"
            f'*Max value may vary slightly depending on the locked parameter stats'
            f'\n```'
        )
    )

    # Set Bonus
    if equip_set := equipment.equipment_set:
        container.add_item(
            ui.TextDisplay(
                f'**{equip_set.name}**\n```\n'
                f'{"\n".join(
                    f'{effect.equipment_count} Pieces: {param_string(effect.parameter, cs)}'
                    for effect in equip_set.set_effects)
                }'
                '\n```'
            )
        )

    # UW
    if isinstance(equipment, schemas.UniqueWeapon):
        container.add_item(
            ui.TextDisplay(
                '**Unique Passive Effect**\n```\n'
                f'{"\n".join(f'{param_string(param, cs)}' for param in equipment.uw_bonus)}'
                '\n```'
            )
        ).add_item(
            ui.TextDisplay(
                '**Unique Weapon Skills**\n```\n'
                f'{"\n".join(f'- {k}: {remove_linebreaks(v)}' for k, v in equipment.uw_descriptions.model_dump().items())}'
                '\n```'
            )
        )

    return container

async def equipment_option_map(equip_string: str, language: enums.Language, cs: schemas.CommonStrings) -> dict[str, ui.Container]:
    pass

async def equip_embed(equip_data: schemas.APIResponse[schemas.Equipment|schemas.UniqueWeapon], session: AsyncSession, cs: schemas.CommonStrings, upgrade=0, upgrade_coeff=1):
    equipment = equip_data.data
    description = StringIO()

    equip_type = cs.equip_type[equipment.slot]
    if equipment.slot == 1:  # weapon
        equip_type = f'{equip_type} ({cs.weapon_type[equipment.job]})'

    rarity_str = enums.ItemRarity(equipment.rarity).name

    # Base Description
    description.write(
        f'Type: {equip_type}\n'
        f'Level: {equipment.level}\n'
        f'Upgrade: {upgrade}\n\n'
    )

    # Stats
    max_value = int(equipment.bonus_parameters * 0.6) + 2  # locking can cause +1/+2
    sub_value = equipment.bonus_parameters - max_value
    mainstat = int(equipment.basestat.value * upgrade_coeff)
    description.write(
        f'**Stats**\n'
        f"```\n{cs.battle_param[equipment.basestat.type]}: {mainstat:,} (Base: {equipment.basestat.value:,})\n"
        f"Bonus Parameters: {equipment.bonus_parameters:,}\n"
        f"Max: {max_value:,}\n"
        f"Sub: {sub_value:,}```\n"
    )

    # Set Bonus
    if equip_set := equipment.equipment_set:
        description.write(f'**{equip_set.name}**\n```\n')
        description.write(
            "\n".join(
                f"{effect.equipment_count} Pieces: {param_string(effect.parameter, cs)}"
                for effect in equip_set.set_effects
            )
        )
        description.write('```')

    # UW
    if isinstance(equipment, schemas.UniqueWeapon):
        description.write('**Unique Passive Effect**\n```\n')
        description.write('\n'.join(param_string(param, cs) for param in equipment.uw_bonus))
        description.write('```')

    return BaseEmbed(
        version=equip_data.version,
        title=f'{await to_emoji(session, rarity_str)} {rarity_str} {equipment.name}',
        description=description.getvalue(),
        color=Color.blurple()
    ).set_thumbnail(url=EQUIPMENT_THUMBNAIL.format(equip_id=equipment.icon_id))

async def uw_embed(equipment_data: schemas.APIResponse[schemas.UniqueWeapon], session: AsyncSession):
    '''UW Descriptions Embed'''
    return BaseEmbed(
        equipment_data.version,
        title=f'{await to_emoji(session, equipment_data.data.rarity)} {equipment_data.data.rarity} {equipment_data.data.name}',
        description=await get_uw_skill_text(equipment_data.data.uw_descriptions, session),
        color=Color.blurple()
    )

async def cost_description(costs: schemas.EquipmentCosts, start_level: int=0, start_upgrade: int=0, start_rarity: int=0):
    description = StringIO()
    total_items = ItemCounter(blacklist=[9])
    synth_items = ItemCounter()
    enhance_items = ItemCounter(blacklist=[9])
    upgrade_items = ItemCounter()

    start_rarity_str = enums.ItemRarity(start_rarity).name
    target_rarity_str = enums.ItemRarity(costs.equipment.rarity).name

    description.write(
        f'**Base Equipment:** {f'{start_rarity_str} {start_level}+{start_upgrade}' if start_rarity else 'None'}\n'
        f'**Target Equipment:** {target_rarity_str} {costs.equipment.level}+{costs.upgrade_costs.upgrades[-1].upgrade_level if costs.upgrade_costs.upgrades else 0}\n\n'
    )

    # Costs
    if costs.synthesis_costs and start_rarity == 0:
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
        raise BotError(f'Starting {start_rarity_str} rarity item cannot be upgraded to {target_rarity_str}')

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
        description.write(f'{' '.join(await synth_items.get_total_strings())}\n\n')
        total_items.add_items(synth_items)

    if enhance_items:
        description.write('**Enhance Costs**\n')
        description.write(f'{' '.join(await enhance_items.get_total_strings())}\n\n')
        total_items.add_items(enhance_items)

    if upgrade_items:
        description.write('**Upgrade Costs**\n')
        description.write(f'{' '.join(await upgrade_items.get_total_strings())}\n\n')
        total_items.add_items(upgrade_items)

    if total_items:
        description.write('**Total Costs**\n')
        description.write(f'{' '.join(await total_items.get_total_strings())}')
    else:
        description.write('No costs')

    return description.getvalue()

async def upgrade_embed(upgrade_data: schemas.APIResponse[schemas.EquipmentCosts], session: AsyncSession, start_level=0, start_upgrade=0, start_rarity=0):
    costs = upgrade_data.data
    equipment = costs.equipment
    rarity_str = enums.ItemRarity(equipment.rarity).name

    return BaseEmbed(
        upgrade_data.version,
        title = f'{await to_emoji(session, rarity_str)} {rarity_str} {equipment.name}',
        description=await cost_description(costs, start_level, start_upgrade, start_rarity),
        color=Color.blurple()
    )

async def equipment_view(interaction: Interaction, equip_string: str, session: AsyncSession, cs: schemas.CommonStrings, language: enums.Language):
    embed_dict = {}
    embed_dict['Equipment Details'] = []
    embed_dict['Costs'] = []
    equip_type, results = parse_equip_string(equip_string)

    if len(results) > 5:
        raise BotError('Too many equipment strings. Maximum of 5 allowed.')

    equipments: list[schemas.APIResponse[schemas.Equipment]]|list[schemas.APIResponse[schemas.UniqueWeapon]] = []
    upgrades: list[schemas.APIResponse[schemas.EquipmentCosts]] = []
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
        if enums.ItemRarity[eqp_args.rarity].value < enums.ItemRarity[results[0].rarity].value:
            raise BotError(
                'Equipment rarity cannot be lower than the first equipment. Was given:\n'
                f'{'\n'.join(f'{i}. `{equip.rarity} {equip.level}+{equip.upgrade}`' for i, equip in enumerate(results))}'
            )
        equipment_data = await find_equipment(equip_type, eqp_args, language)
        upgrade_data = await get_upgrade_costs(equipment_data.data.equip_id, eqp_args.upgrade, language)
        equipments.append(equipment_data)
        upgrades.append(upgrade_data)

    for equipment_data, upgrade_data in zip(equipments, upgrades):
        if upgrade_costs := upgrade_data.data.upgrade_costs.upgrades:  # upgrade > 0
            upgrade_level = upgrade_costs[-1].upgrade_level
            coefficient = upgrade_costs[-1].coefficient
            embed_dict['Equipment Details'].append(await equip_embed(equipment_data, session, cs, upgrade_level, coefficient))
        else:
            embed_dict['Equipment Details'].append(await equip_embed(equipment_data, session, cs))

    if len(equipments) == 1:
        embed_dict['Costs'].append(await upgrade_embed(upgrade_data, session))
    else:
        for upgrade_data in upgrades[1:]:
            embed_dict['Costs'].append(await upgrade_embed(upgrade_data, session, results[0].level, results[0].upgrade, enums.ItemRarity[results[0].rarity].value))

    # UW descriptions
    if isinstance(equipments[0].data, schemas.UniqueWeapon):
        embed_dict['UW Skills'] = [await uw_embed(equipments[0], session)]

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
        "/equipment armor ssr240+120\n=> Type: Chest, Rarity: SSR, Level: 240, Upgrade Level:120\n"
        "/equipment aa UR300\n=> Type: A.A.'s UW, Rarity: UR, Level: 300, Upgrade Level:0\n"
        "/equipment sword LR+240\n=> Type: Sword, Rarity: LR, Level: 240, Upgrade Level:240```"
    )

    return text.getvalue()


