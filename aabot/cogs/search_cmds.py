from typing import List, Optional
import discord
from discord import app_commands
from discord.ext import commands
from collections import Counter
from io import StringIO

import common
import quests
from master_data import MasterData
from helper import human_format as hf
from emoji import emoji_list, soul_emoji, rarity_emoji
from pagination import MixedView, show_view
from items import get_item_name, get_item_list, Item
from equipment import get_equipment_from_str, Equipment, get_upgrade_costs
from cogs.char_cmds import IdTransformer
from character import find_id_from_name
from main import AABot

# soul bonus
def get_bonus_url(soul_list):
    bonus_url = common.raw_asset_link_header + 'Soul_Bonus/bonus'
    c = Counter(soul_list)
    souls = sorted([c[1], c[2], c[3], c[4]], reverse=True)  # normal souls
    light = c[5]
    dark = c[6]
    
    first = souls[0] + light
    bonus = None
    if first == 3:
        if souls[1] == 2: # 3+2
            bonus = 2
        else:  # 3
            bonus = 1
    elif first == 4:  # 4
        bonus = 3
    elif first == 5:  # 5
        bonus = 4
    
    if bonus:
        bonus_url += f"_{bonus}"
    if dark:
        bonus_url += f"_{dark+4}"
    bonus_url += '.png'
    return bonus_url

#########################
# enemy search
#########################

def basic_enemy_field(master: MasterData, enemy: dict)->dict:
    '''
    returns a basic embed field for an enemy
    '''
    batp = enemy['BattleParameter']
    basp = enemy['BaseParameter']
    rarity = common.char_rarity.get(enemy['CharacterRarityFlags'])
    soul = soul_emoji.get(enemy.get('ElementType'))

    name = f"[{rarity}] Lv.{enemy['EnemyRank']} {master.search_string_key(enemy['NameKey'])} {soul}"
    value = (
                f"**:crossed_swords:** {hf(batp['AttackPower'])} **:heart:** {hf(batp['HP'])} "
                f"**:shield:** {hf(batp['Defense'])}\n**Speed:** {batp['Speed']}\n"
                f"**{emoji_list['str']}** {hf(basp['Muscle'])} **{emoji_list['dex']}** {hf(basp['Energy'])} "
                f"**{emoji_list['mag']}** {hf(basp['Intelligence'])} **{emoji_list['sta']}** {hf(basp['Health'])}"
            )
    
    return {'name': name, 'value': value, 'inline': False}

def parameter_text(parameter: dict, parameter_map: dict)->str:
    text = '```json\n'
    for k, v in parameter_map.items():
        
        if k in common.battle_parameter_percentage:  # % stats, stat/100(%)
            stat_text = f"{k}: {parameter[v]/100}%"
        else:
            stat_text = f"{k}: {parameter[v]}"

        if k in common.battle_parameter_left:
            text += f"{stat_text:<27}"
        elif k in common.battle_parameter_right:
            text += f"{'':<27}{stat_text:<22}\n"
        else:
            text += f"{stat_text:<22}\n"

    text += '```'
    return text

def detailed_enemy_embed(master: MasterData, enemy: dict)->discord.Embed:
    rarity = common.char_rarity.get(enemy['CharacterRarityFlags'])
    soul = soul_emoji.get(enemy.get('ElementType'))
    name = f"[{rarity}] Lv.{enemy['EnemyRank']} {master.search_string_key(enemy['NameKey'])} {soul}"

    embed = discord.Embed(
        title=name,
        color=discord.Colour.red()
    )

    embed.add_field(
        name='Base Parameters',
        value=parameter_text(enemy['BaseParameter'], common.base_parameter_map),
        inline=False)
    embed.add_field(
        name='Battle Parameters',
        value=parameter_text(enemy['BattleParameter'], common.battle_parameter_map1) \
            + parameter_text(enemy['BattleParameter'], common.battle_parameter_map2),
        inline=False)
    if (icontype := enemy["UnitIconType"]) == 0:
        embed.set_thumbnail(
            url=common.raw_asset_link_header+f"Characters/Sprites/CHR_000{enemy['UnitIconId']:03}_00_s.png")
    elif icontype == 1:
        embed.set_thumbnail(
            url=common.raw_asset_link_header+f"Enemy/ENE_000{enemy['UnitIconId']:03}.png")
    else:
        embed.set_thumbnail(
            url=common.raw_asset_link_header+f"Characters/Sprites/CHR_000{enemy['UnitIconId']:03}_01_s.png")
    return embed

def quest_embed(master: MasterData, quest_data, bp)->discord.Embed:
    embed = discord.Embed(
        title=f"Stage {quests.convert_to_stage(quest_data['Id'])} (ID: {quest_data['Id']})",
        description=(f"**BP:** {bp:,}\n"
                     f"**Daily red orb gain:** {quest_data['PotentialJewelPerDay']}"),
        color=discord.Colour.red()
    )

    return embed

def tower_embed(master: MasterData, quest_data: dict, tower_type: str, bp: int)->discord.Embed:
    fixed_rewards = get_item_list(master, quest_data['BattleRewardsConfirmed'])
    first_time_rewards = get_item_list(master, quest_data['BattleRewardsFirst'])

    text = ''
    if fixed_rewards:
        text += '**Fixed Rewards:**\n'
        for reward in fixed_rewards:
            text += f"-{reward}\n"
    if first_time_rewards:
        text += '**First Time Rewards:**\n'
        for reward in first_time_rewards:
            text += f"-{reward}\n"

    embed = discord.Embed(
        title=f"Tower of {tower_type} - Floor {quest_data['Floor']}",
        description=f"**BP:** {bp:,}\n{text}",
        color=discord.Colour.red()
    )

    return embed

def add_resonance(embed:discord.Embed, def_list: List):
    '''adds resonance indication to the enemy embed'''
    resonance = ' | <:resonance:1067010707561926696>'
    if len(def_list) > 1:
        min_ind = def_list.index(min(def_list))
        min_field = embed.fields[min_ind]
        embed.set_field_at(
            min_ind, name=min_field.name+resonance+' (Low)', 
            value=min_field.value, inline=min_field.inline)

        max_ind = def_list.index(max(def_list))
        max_field = embed.fields[max_ind]
        embed.set_field_at(
            max_ind, name=max_field.name+resonance+' (High)', 
            value=max_field.value, inline=max_field.inline)


#########################
# Equipment
#########################

def equipment_help_embed():
    embed = discord.Embed(
        title=f"Equipment Command Help",
        description="If you find an error with the command please report it on https://discord.gg/DyATxE7saX.",
        color=discord.Colour.green()
    )
    
    embed.add_field(
        name="String Parameters",
        value=(
            "Provides details for equipment rarity, level, and upgrade level.\n"
            "**Rarity**: D, C, B, A, S, SP(S+), R, SR, SSR, UR, LR. Lowercase is allowed.\n\n"
            "**Level**: integer for the gear level. If the level doesn't exist will return error.\n\n"
            "**Upgrade Level**: Upgrade Level of gear. Integer after '+' prefix (Ex: +120). Will default to 0 if not provided. Additionally it is possible to omit the equipment level and write only the upgrade level. This will assume the upgrade level is the same as the equipment level.\n\n"
            "```Examples: \n"
            "ssr240+120 -> Rarity: SSR Level: 240 Upgrade Level:120\n"
            "UR300 -> Rarity: UR Level: 300 Upgrade Level:0\n"
            "LR+240 -> Rarity: LR Level: 240 Upgrade Level:240```"
            )
    )
    
    embed.add_field(
        name="Additional Parameters",
        value=(
            "Additional Information that may be required to find equipment.\n"
            "**Type**: The type of equipment. If the character is specified this field is unneeded.\n\n"
            "**Character**: Character name or id. Character is only used to find UW."
            "This field can be combined into input string by writing `[character] [string_parameter]` instead of a normal string paramater. Additionaly having a charcter field will overwrite any Type field parameters." 
        )
    )
    
    embed.add_field(
        name="Equipment Upgrade Cost",
        value=(
            "Equipment upgrade costs will be also calculated\n"
            "By default it will show the cost of making the specified equipment."
            "However adding a 2nd equipment string will allow you to compare and upgrade from the first equipment. The first equipment must be lower level than the 2nd.\n\n"
            
            "```Examples: \n"
            "aa ssr180+120 -> will show costs up to ssr240+120\n"
            "aa ssr180+180 LR240+240 -> will show costs from ssr180+180 to LR240+240```"
        )
    )

    return embed

def equipment_embed(equipment: Equipment):
    embed = discord.Embed(
        title=f"{rarity_emoji.get(equipment.rarity, rarity_emoji.get('N'))} {equipment.rarity} {equipment.name}",
        description=f"Type: {equipment.equip_type}\nLevel: {equipment.level}\nUpgrade: {equipment.upgrade_level}",
        color=discord.Colour.blurple()
    )
    
    max_value = int(equipment.bonus_parameters * 0.6)
    sub_value = equipment.bonus_parameters - max_value

    stats_value = (
        f"```{equipment.stat_type}: {equipment.stat:,} (Base: {equipment.basestat:,})\n"
        f"Bonus Parameters: {equipment.bonus_parameters:,}\n"
        f"Max: {max_value:,}\n"
        f"Sub: {sub_value:,}```"
    )
    embed.add_field(
        name="Stats",
        value=stats_value,
        inline=False  # Display as a separate block
    )


    if equipment.set_name:
        set_effect = "\n".join([f"{set_piece[0]}: {set_piece[1]} {set_piece[2]}" for set_piece in equipment.set_effect])
        embed.add_field(
            name=equipment.set_name,
            value=f"```{set_effect}```",
            inline=False 
        )
        
    if equipment.is_uw:    
        uw_bonus_effect = "\n".join([f"{bonus[0]}: {bonus[1]}" for bonus in equipment.uw_bonus])
        embed.add_field(
            name="Unique Passive Effect",
            value=f"```{uw_bonus_effect}```",
            inline=False
        )
        
    # thumbnail
    image_link = common.raw_asset_link_header + f'Equipment/EQP_{equipment.icon:06}.png'
    embed.set_thumbnail(url=image_link)
    
    return embed

def upgrade_embed(costs: dict[str, Item], equip1: Equipment, equip2: Equipment=None):
    
    title_text = (
            f"{equip1.rarity} Lv. {equip1.level}+{equip1.upgrade_level} → "
            f"{equip2.rarity} Lv. {equip2.level}+{equip2.upgrade_level}"
            ) if equip2 else f"{equip1.rarity} Lv. {equip1.level}+{equip1.upgrade_level}"
    
    embed = discord.Embed(
        title= title_text,
        description=f'Type: {equip1.equip_type}',
        color=discord.Colour.blurple()
    )
    
    if equip2:
        embed.add_field(
            name='Stats',
            value=(
                f"```{equip1.stat_type}: {equip1.stat:,} -> {equip2.stat:,}\n"
                f"Bonus Parameters: {equip1.bonus_parameters:,} -> {equip2.bonus_parameters:,}```"
            )
        )
    
    if costs:
        upgrade_costs = StringIO()
        upgrade_costs.write('```')
        for item in costs.values():
            upgrade_costs.write(f"{item}\n")
        upgrade_costs.write('```')
        
        embed.add_field(
            name="Upgrade Costs",
            value=upgrade_costs.getvalue(),
            inline=False
        )
    
    return embed

class Search(commands.Cog, name='Search Commands'):
    '''Commands related to searching'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
        stage='Quest stage id or string(ex.18-28)'
    )
    async def quest(self, interaction: discord.Interaction, stage: str):
        '''
        Searches quest and enemy data for specified stage

        Shows an overview as the main page and can select to see in detail
        '''
        quest_id = quests.convert_from_stage(stage)
        quest_data = quests.get_quest(self.bot.masterdata, quest_id)
        embed_dict = {}

        if not quest_data:  # invalid stage
            embed = discord.Embed(
                title='Stage not Found',
                description=f'Could not find stage {stage}',
                color=discord.Colour.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        quest_enemy_list = quests.get_quest_enemy(self.bot.masterdata, quest_id)

        # calculate bp first
        bp = 0 
        for enemy in quest_enemy_list:
            bp += enemy['BattlePower']
        
            
        embed = quest_embed(self.bot.masterdata, quest_data, bp)

        def_list = []  # for mimi resonance
        soul_list = [] # for soul bonus
        detail_embeds = [] # embed list for enemy details

        for enemy in quest_enemy_list:
            def_list.append(enemy['BattleParameter']['Defense'])
            soul_list.append(enemy['ElementType'])
            embed.add_field(**basic_enemy_field(self.bot.masterdata, enemy))
            detail_embeds.append(detailed_enemy_embed(self.bot.masterdata, enemy))
        
        add_resonance(embed, def_list)  #add resonance indication

        embed.set_thumbnail(url=get_bonus_url(soul_list))
        
        embed_dict['Quest Data'] = [embed]
        embed_dict['Enemy Data'] = detail_embeds

        user = interaction.user
        view = MixedView(user, embed_dict, 'Quest Data')
        await show_view(interaction, view)

    @app_commands.command()
    @app_commands.describe(
        floor='The floor of the tower',
        towertype="The tower type. Defaults to the Tower of Infinity"
    )
    async def tower(
        self, interaction: discord.Interaction, 
        floor: int, 
        towertype: Optional[common.Tower]=common.Tower.Infinity):
        '''
        Searches enemy data for specified tower floor

        Shows an overview as the main page and can select to see in detail
        '''
        quest_data = quests.get_tower_floor(self.bot.masterdata, floor, towertype)
        embed_dict = {}

        if not quest_data:  # invalid stage
            embed = discord.Embed(
                title='Floor not Found',
                description=f'Could not find Tower of {towertype.name} floor {floor}',
                color=discord.Colour.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        quest_enemy_list = quests.get_tower_enemy(self.bot.masterdata, quest_data['EnemyIds'])

        # calculate bp first
        bp = 0 
        for enemy in quest_enemy_list:
            bp += enemy['BattlePower']

        embed = tower_embed(self.bot.masterdata, quest_data, towertype.name, bp)

        def_list = []  # for mimi resonance
        soul_list = [] # for soul bonus
        detail_embeds = [] # embed list for enemy details
        for enemy in quest_enemy_list:
            def_list.append(enemy['BattleParameter']['Defense'])
            soul_list.append(enemy['ElementType'])
            embed.add_field(**basic_enemy_field(self.bot.masterdata, enemy))
            detail_embeds.append(detailed_enemy_embed(self.bot.masterdata, enemy))
        
        add_resonance(embed, def_list)  #add resonance indication

        embed.set_thumbnail(url=get_bonus_url(soul_list))
        
        embed_dict['Quest Data'] = [embed]
        embed_dict['Enemy Data'] = detail_embeds 

        user = interaction.user
        view = MixedView(user, embed_dict, 'Quest Data')
        await show_view(interaction, view)

    @app_commands.command()
    @app_commands.describe(
        id='Item id',
        type="Item type",
        language="Text language. Defaults to English."
    )
    async def finditem(
        self, interaction: discord.Interaction, 
        id: int, 
        type: int,
        language: Optional[common.Language]=common.Language.EnUs):
        '''
        Command for quick searching from ItemId and ItemType
        '''

        item = self.bot.masterdata.find_item(id, type)
        name = get_item_name(self.bot.masterdata, item, language)
        await interaction.response.send_message(name)
        
    @app_commands.command()
    @app_commands.describe(
        string="Search string.",
        type="Equipment Type. Can also specify in string.",
        character="For UW search. Can also specify in string and ignore type.",
        language="Text language. Defaults to English."
    )    
    async def equipment(
        self, interaction: discord.Interaction, 
        string: str,
        type: Optional[common.EquipSlot]=None,
        character: Optional[app_commands.Transform[int, IdTransformer]]=None,
        language: Optional[common.Language]=common.Language.EnUs
    ):
        if not type and not character:  # char + string input
            tokens = string.split()
            
            if len(tokens) == 1:
                await interaction.response.send_message(embed=equipment_help_embed(), ephemeral=True)
                return
            character = find_id_from_name(tokens[0])
            equip_strings = tokens[1:]
        else:
            equip_strings = string.split()
        
        if type:
            slot = type.value.SlotType
            job = type.value.EquippedJobFlags
        elif character:
            slot = 1  # weapon
            job = None
        else:  # undefined 
            await interaction.response.send_message(embed=equipment_help_embed(), ephemeral=True)
            return
        
        equipments: List[Equipment] = []
        embed_dict = {}
        equipment_embeds = []
        for i, equip_str in enumerate(equip_strings, 1):
            if i == 3:
                await interaction.response.send_message(embed=equipment_help_embed(), ephemeral=True)
                return
            equipment: Equipment = get_equipment_from_str(slot, equip_str, self.bot.masterdata, language, char_id=character, job=job)
            
            if not equipment:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"Equipment {i} was not found correctly",
                        description=f"Search parameters: string: `{string}`, Character: {character}, Type: {type}. If you feel that this is a bug feel free to report in on the [support server](https://discord.gg/DyATxE7saX)"
                    )
                )
                return
            
            equipments.append(equipment)
            equipment_embeds.append(equipment_embed(equipment))
        
        if len(equipments) == 1:
            upgrade_costs = get_upgrade_costs(self.bot.masterdata, equipments[0])
            upgrade_ebd = upgrade_embed(upgrade_costs, equipments[0])
        else:
            upgrade_costs = get_upgrade_costs(self.bot.masterdata, equipments[0], equipments[1])
            upgrade_ebd = upgrade_embed(upgrade_costs, equipments[0], equipments[1])
        
        embed_dict['Equipment Details'] = equipment_embeds
        embed_dict['Upgrade Costs'] = [upgrade_ebd]
            
        user = interaction.user
        view = MixedView(user, embed_dict, 'Equipment Details')
        await show_view(interaction, view)

async def setup(bot):
	await bot.add_cog(Search(bot))