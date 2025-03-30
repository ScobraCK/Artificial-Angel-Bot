from collections import Counter
from discord import Embed, Color, Interaction
from io import StringIO
from typing import List

from aabot.api import response as resp, api
from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import MixedView
from aabot.utils import emoji
from aabot.utils.assets import RAW_ASSET_BASE, SOUL_BONUS
from aabot.utils.utils import human_format as hf, from_quest_id, decimal_format


def get_bonus_url(soul_list):
    c = Counter(soul_list)
    souls = sorted([c[1], c[2], c[3], c[4]], reverse=True)  # normal souls
    light = c[5]
    dark = c[6]
    
    first = souls[0] + light
    bonus = ''
    if first == 3:
        if souls[1] == 2: # 3+2
            bonus = '2'
        else:  # 3
            bonus = '1'
    elif first == 4:
        bonus = '3'
    elif first == 5:
        bonus = '4'
    
    if dark:
        bonus = f"{bonus}_{dark+4}"
        
    bonus_url = SOUL_BONUS.format(bonus=bonus)
    return bonus_url

def basic_enemy_field(enemy: resp.Enemy)->dict:
    '''
    returns a basic embed field for an enemy
    '''
    soul_emj = emoji.soul_emoji.get(enemy.element)  # TODO I made a big mistake
    name = f"[{enemy.rarity}] Lv.{enemy.level} {enemy.name} {soul_emj}"
    value = (
                f":crossed_swords: {hf(enemy.battle_params.attack)} :heart: {hf(enemy.battle_params.hp)} "
                f":shield: {hf(enemy.battle_params.defense)}\n"
                f"**Speed:** {enemy.battle_params.speed}\n"
                f"**{emoji.emoji_list['str']}** {hf(enemy.base_params.str)} "
                f"**{emoji.emoji_list['dex']}** {hf(enemy.base_params.dex)} "
                f"**{emoji.emoji_list['mag']}** {hf(enemy.base_params.mag)} "
                f"**{emoji.emoji_list['sta']}** {hf(enemy.base_params.sta)}"
            )
    
    return {'name': name, 'value': value, 'inline': False}

def base_param_text(params: resp.BaseParameters)->str:
    text = (
        f'```json\n'
        f'STR: {params.str:,}\n'
        f'DEX: {params.dex:,}\n'
        f'MAG: {params.mag:,}\n'
        f'STA: {params.sta:,}```'
    )
    return text

def battle_param_text(params: resp.BattleParameters)->str:
    text = (
        f'```json\n'
        f'HP: {params.hp:,}\n'
        f'ATK: {params.attack:,}\n'
        f'DEF: {params.defense:,}\n'
        f'DEF Break: {params.def_break:,}\n'
        f'SPD: {params.speed:,}\n'
        f'```'
        f'```json\n'
        f'{f"PM.DEF Break: {params.def_break:,}":<24}{f"P.DEF: {params.pdef:,}":<22}\n'
        f'{"":<24}{f"M.DEF: {params.mdef:,}":<22}\n'
        f'{f"ACC: {params.acc:,}":<24}{f"EVD: {params.evade:,}":<22}\n'
        f'{f"CRIT: {params.crit:,}":<24}{f"CRIT RES: {params.crit_res:,}":<22}\n'
        f'{f"CRIT DMG Boost: {decimal_format(params.crit_dmg)}%":<24}{f"P.CRIT DMG Cut: {decimal_format(params.pcut)}%":<22}\n'
        f'{"":<24}{f"M.CRIT DMG Cut: {decimal_format(params.mcut)}%":<22}\n'
        f'{f"Debuff ACC: {params.debuff_acc:,}":<24}{f"Debuff RES: {params.debuff_res:,}":<22}\n'
        f'{f"Counter: {decimal_format(params.counter)}%":<24}{f"HP Drain: {decimal_format(params.hp_drain)}%":<22}\n'
        f'```'
    )
    return text

def detailed_enemy_embed(enemy: resp.Enemy, version: str)->Embed:
    soul_emj = emoji.soul_emoji.get(enemy.element)  # TODO I made a big mistake
    name = f"[{enemy.rarity}] Lv.{enemy.level} {enemy.name} {soul_emj}"

    embed = BaseEmbed(
        version,
        title=name,
        color=Color.red()
    )

    embed.add_field(
        name='Base Parameters',
        value=base_param_text(enemy.base_params),
        inline=False)
    embed.add_field(
        name='Battle Parameters',
        value=battle_param_text(enemy.battle_params),
        inline=False)
    embed.add_field(
        name='Skills',
        value=(
            f'```json\n'
            f"Actives: {enemy.actives}\n"
            f"Passives: {enemy.passives}\n"
            f"UW Rarity: {enemy.uw_rarity}\n"
            f'```'
        )
    )
    if (icontype := enemy.icon_type) == 0:
        embed.set_thumbnail(
            url=RAW_ASSET_BASE+f"Characters/Sprites/CHR_{enemy.icon_id:06}_00_s.png")
    elif icontype == 1:
        embed.set_thumbnail(
            url=RAW_ASSET_BASE+f"Enemy/ENE_{enemy.icon_id:06}.png")
    else:
        embed.set_thumbnail(
            url=RAW_ASSET_BASE+f"Characters/Sprites/CHR_{enemy.icon_id:06}_01_s.png")
    return embed

def add_resonance(embed:Embed, def_list: List):
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

def quest_view(interaction: Interaction, quest_data: resp.APIResponse[resp.Quest])->MixedView:
    embed_dict = {}
    quest = quest_data.data

    # Quest Data
    main_embed = BaseEmbed(
        quest_data.version,
        title=f"Stage {from_quest_id(quest.quest_id)} (ID: {quest.quest_id})", 
    )
    bp = 0
    def_list = []
    for enemy in quest.enemy_list:
        main_embed.add_field(**basic_enemy_field(enemy))
        def_list.append(enemy.battle_params.defense)
        bp += enemy.bp

    main_embed.description = f"**BP:** {bp:,}\n**Daily red orb gain:** {quest.red_orb}"
    add_resonance(main_embed, def_list)

    # Enemy Data
    enemy_embeds = []
    for enemy in quest.enemy_list:
        enemy_embeds.append(detailed_enemy_embed(enemy, quest_data.version))

    embed_dict['Quest Data'] = [main_embed]
    embed_dict['Enemy Data'] = enemy_embeds
    
    return MixedView(interaction.user, embed_dict, 'Quest Data')

async def tower_view(interaction: Interaction, tower_data: resp.APIResponse[resp.Tower])->MixedView:
    embed_dict = {}
    tower = tower_data.data
    fixed_rewards = tower.fixed_rewards
    first_time_rewards = tower.first_rewards

    description = StringIO()

    main_embed = BaseEmbed(
        tower_data.version,
        title=f"Tower of {tower.tower_type} - Floor {tower.floor}",
        color=Color.red()
    )

    bp = 0
    def_list = []
    for enemy in tower.enemy_list:
        main_embed.add_field(**basic_enemy_field(enemy))
        def_list.append(enemy.battle_params.defense)
        bp += enemy.bp

    description.write(f"**BP:** {bp:,}\n")

    if fixed_rewards:
        description.write('**Fixed Rewards:**\n')
        for reward in fixed_rewards:
            item = await api.fetch_item(reward.item_id, reward.item_type)
            description.write(f"-{reward.count:,}x {item.data.name}\n")
    if first_time_rewards:
        description.write('**First Time Rewards:**\n')
        for reward in first_time_rewards:
            item = await api.fetch_item(reward.item_id, reward.item_type)
            description.write(f"-{reward.count:,}x {item.data.name}\n")

    main_embed.description = description.getvalue()
    add_resonance(main_embed, def_list)

    enemy_embeds = []
    for enemy in tower.enemy_list:
        enemy_embeds.append(detailed_enemy_embed(enemy, tower_data.version))

    embed_dict['Tower Data'] = [main_embed]
    embed_dict['Enemy Data'] = enemy_embeds
    
    return MixedView(interaction.user, embed_dict, 'Tower Data')

