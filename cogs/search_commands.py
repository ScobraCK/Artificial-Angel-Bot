from typing import List, Optional
import discord
from discord import app_commands
from discord.ext import commands
from collections import Counter

import common
import quests, items
from master_data import MasterData
from helper import human_format as hf
from emoji import emoji_list, soul_emoji
from my_view import My_View

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
    value = f"**:crossed_swords:** {hf(batp['AttackPower'])} **:heart:** {hf(batp['HP'])} \
        **:shield:** {hf(batp['Defense'])}\n**Speed:** {batp['Speed']}\n\
        **{emoji_list['str']}** {hf(basp['Muscle'])} **{emoji_list['dex']}** {hf(basp['Energy'])} \
        **{emoji_list['mag']}** {hf(basp['Intelligence'])} **{emoji_list['sta']}** {hf(basp['Health'])}"
    
    return {'name': name, 'value': value, 'inline': False}

def parameter_text(parameter: dict, parameter_map: dict)->str:
    text = '```json\n'
    for k, v in parameter_map.items():
        stat_text = f"{k}: {parameter[v]}"
        if k in common.battle_parameter_percentage:
            stat_text += '%'
        if k in common.battle_parameter_left:
            text += f"{stat_text:<25}"
        elif k in common.battle_parameter_right:
            text += f"{'':<25}{stat_text:<20}\n"
        else:
            text += f"{stat_text:<20}\n"

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
            url=common.raw_asset_link_header+f"Characters/CHR_000{enemy['UnitIconId']:03}_00_s.png")
    elif icontype == 1:
        embed.set_thumbnail(
            url=common.raw_asset_link_header+f"Enemy/ENE_000{enemy['UnitIconId']:03}.png")
    else:
        embed.set_thumbnail(
            url=common.raw_asset_link_header+f"Characters/CHR_000{enemy['UnitIconId']:03}_01_s.png")
    return embed

def quest_embed(master: MasterData, quest_data, bp)->discord.Embed:
    embed = discord.Embed(
        title=f"Stage {quests.convert_to_stage(quest_data['Id'])}",
        description=f"**BP:** {bp:,}\n\
            **Daily red orb gain:** {quest_data['PotentialJewelPerDay']}",
        color=discord.Colour.red()
    )

    return embed

def tower_embed(master: MasterData, quest_data: dict, tower_type: str, bp: int)->discord.Embed:
    fixed_rewards = items.get_reward_list(master, quest_data['BattleRewardsConfirmed'])
    first_time_rewards = items.get_reward_list(master, quest_data['BattleRewardsFirst'])

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

class Enemy_View(My_View):
    def __init__(self, user: discord.User, main_embed: discord.Embed, embeds:List[discord.Embed]):
        super().__init__(user)
        self.main_embed = main_embed
        self.embeds = embeds
        self.length = len(embeds)

    async def update_button(self, button: discord.ui.Button):
        for i, btn in enumerate(self.children):
            if btn is button or i > self.length:
                btn.disabled=True
            else:
                btn.disabled=False

    @discord.ui.button(label="Main", disabled=True, row=1)
    async def main_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.main_embed, view=self)

    @discord.ui.button(label="1")
    async def btn1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[0], view=self)
        
    @discord.ui.button(label="2")
    async def btn2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[1], view=self)

    @discord.ui.button(label="3")
    async def btn3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[2], view=self)
    
    @discord.ui.button(label="4")
    async def btn4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[3], view=self)

    @discord.ui.button(label="5")
    async def btn5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[4], view=self)

    

class Search(commands.Cog, name='Search Commands'):
    '''Commands related to searching'''

    def __init__(self, bot):
        self.bot = bot

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
        
        # show min max defense resonance
        resonance = ' | <:resonance:1067010707561926696>'
        if len(def_list) > 1:
            def_index = sorted(range(len(def_list)), key=def_list.__getitem__)
            min = def_index[0]
            min_field = embed.fields[min]
            embed.set_field_at(
                min, name=min_field.name+resonance, 
                value=min_field.value, inline=min_field.inline)

            max = def_index[-1]
            max_field = embed.fields[max]
            embed.set_field_at(
                max, name=max_field.name+resonance, 
                value=max_field.value, inline=max_field.inline)

        embed.set_thumbnail(url=get_bonus_url(soul_list))

        user = interaction.user
        view = Enemy_View(user, embed, detail_embeds)
        await view.update_button(view.main_btn)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

    @app_commands.command()
    @app_commands.describe(
        floor='The floor of the tower',
        tower="The tower type. Defaults to the Tower of Infinity"
    )
    async def tower(
        self, interaction: discord.Interaction, 
        floor: int, 
        tower: Optional[common.Tower]=common.Tower.Infinity):
        '''
        Searches enemy data for specified tower floor

        Shows an overview as the main page and can select to see in detail
        '''
        quest_data = quests.get_tower_floor(self.bot.masterdata, floor, tower)

        if not quest_data:  # invalid stage
            embed = discord.Embed(
                title='Floor not Found',
                description=f'Could not find Tower of {tower.name} floor {floor}',
                color=discord.Colour.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        quest_enemy_list = quests.get_tower_enemy(self.bot.masterdata, quest_data['EnemyIds'])

        # calculate bp first
        bp = 0 
        for enemy in quest_enemy_list:
            bp += enemy['BattlePower']

        embed = tower_embed(self.bot.masterdata, quest_data, tower.name, bp)

        def_list = []  # for mimi resonance
        soul_list = [] # for soul bonus
        detail_embeds = [] # embed list for enemy details
        for enemy in quest_enemy_list:
            def_list.append(enemy['BattleParameter']['Defense'])
            soul_list.append(enemy['ElementType'])
            embed.add_field(**basic_enemy_field(self.bot.masterdata, enemy))
            detail_embeds.append(detailed_enemy_embed(self.bot.masterdata, enemy))
        
        # show min max defense resonance
        resonance = ' | <:resonance:1067010707561926696>'
        if len(def_list) > 1:
            def_index = sorted(range(len(def_list)), key=def_list.__getitem__)
            min = def_index[0]
            min_field = embed.fields[min]
            embed.set_field_at(
                min, name=min_field.name+resonance, 
                value=min_field.value, inline=min_field.inline)

            max = def_index[-1]
            max_field = embed.fields[max]
            embed.set_field_at(
                max, name=max_field.name+resonance, 
                value=max_field.value, inline=max_field.inline)

        embed.set_thumbnail(url=get_bonus_url(soul_list))

        user = interaction.user
        view = Enemy_View(user, embed, detail_embeds)
        await view.update_button(view.main_btn)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Search(bot))