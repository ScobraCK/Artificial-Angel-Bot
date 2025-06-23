from collections import Counter
from io import StringIO

from discord import Color, Embed, Interaction

from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import MixedView
from aabot.utils import api, emoji
from aabot.utils.assets import RAW_ASSET_BASE, SOUL_BONUS
from aabot.utils.utils import decimal_format, from_quest_id, human_format as hf
from common import enums, schemas

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

def basic_enemy_field(enemy: schemas.Enemy)->dict:
    '''
    returns a basic embed field for an enemy
    '''
    soul_emj = emoji.soul_emoji.get(enemy.element)
    name = f"[{enums.CharacterRarity(enemy.rarity).name.replace('Plus', '+')}] Lv.{enemy.level} {enemy.name} {soul_emj}"
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

def base_param_text(params: schemas.BaseParameters, cs: schemas.CommonStrings)->str:
    text = (
        f'```json\n'
        f'{cs.base_param[enums.BaseParameter.STR]}: {params.str:,}\n'
        f'{cs.base_param[enums.BaseParameter.DEX]}: {params.dex:,}\n'
        f'{cs.base_param[enums.BaseParameter.MAG]}: {params.mag:,}\n'
        f'{cs.base_param[enums.BaseParameter.STA]}: {params.sta:,}```'
    )
    return text

def battle_param_text(params: schemas.BattleParameters, cs: schemas.CommonStrings)->str:
    text = (
        f'```json\n'
        f'{cs.battle_param[enums.BattleParameter.HP]}: {params.hp:,}\n'
        f'{cs.battle_param[enums.BattleParameter.ATK]}: {params.attack:,}\n'
        f'{cs.battle_param[enums.BattleParameter.DEF]}: {params.defense:,}\n'
        f'{cs.battle_param[enums.BattleParameter.DEF_BREAK]}: {params.def_break:,}\n'
        f'{cs.battle_param[enums.BattleParameter.SPD]}: {params.speed:,}\n'
        f'```'
        f'```json\n'
        f'{f"{cs.battle_param[enums.BattleParameter.PM_DEF_BREAK]}: {params.pmdb:,}":<24}{f"{cs.battle_param[enums.BattleParameter.P_DEF]}: {params.pdef:,}":<22}\n'
        f'{"":<24}{f"{cs.battle_param[enums.BattleParameter.M_DEF]}: {params.mdef:,}":<22}\n'
        f'{f"{cs.battle_param[enums.BattleParameter.ACC]}: {params.acc:,}":<24}{f"{cs.battle_param[enums.BattleParameter.EVD]}: {params.evade:,}":<22}\n'
        f'{f"{cs.battle_param[enums.BattleParameter.CRIT]}: {params.crit:,}":<24}{f"{cs.battle_param[enums.BattleParameter.CRIT_RES]}: {params.crit_res:,}":<22}\n'
        f'{f"{cs.battle_param[enums.BattleParameter.CRIT_DMG_BOOST]}: {decimal_format(params.crit_dmg)}%":<24}{f"{cs.battle_param[enums.BattleParameter.P_CRIT_DMG_CUT]}: {decimal_format(params.pcut)}%":<22}\n'
        f'{"":<24}{f"{cs.battle_param[enums.BattleParameter.M_CRIT_DMG_CUT]}: {decimal_format(params.mcut)}%":<22}\n'
        f'{f"{cs.battle_param[enums.BattleParameter.DEBUFF_ACC]}: {params.debuff_acc:,}":<24}{f"{cs.battle_param[enums.BattleParameter.DEBUFF_RES]}: {params.debuff_res:,}":<22}\n'
        f'{f"{cs.battle_param[enums.BattleParameter.COUNTER]}: {decimal_format(params.counter)}%":<24}{f"{cs.battle_param[enums.BattleParameter.HP_DRAIN]}: {decimal_format(params.hp_drain)}%":<22}\n'
        f'```'
    )
    return text

def detailed_enemy_embed(enemy: schemas.Enemy, cs: schemas.CommonStrings, version: str)->Embed:
    soul_emj = emoji.soul_emoji.get(enemy.element)  # TODO I made a big mistake
    name = f"[{enemy.rarity}] Lv.{enemy.level} {enemy.name} {soul_emj}"

    embed = BaseEmbed(
        version,
        title=name,
        color=Color.red()
    )

    embed.add_field(
        name='Base Parameters',
        value=base_param_text(enemy.base_params, cs),
        inline=False)
    embed.add_field(
        name='Battle Parameters',
        value=battle_param_text(enemy.battle_params, cs),
        inline=False)
    embed.add_field(
        name='Skills',
        value=(
            f'```json\n'
            f"Actives: {enemy.actives}\n"
            f"Passives: {enemy.passives}\n"
            f"UW Rarity: {enums.ItemRarity(enemy.uw_rarity).name}\n"
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

def add_resonance(embed:Embed, def_list: list):
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

def quest_view(interaction: Interaction, quest_data: schemas.APIResponse[schemas.Quest], cs: schemas.CommonStrings)->MixedView:
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
        enemy_embeds.append(detailed_enemy_embed(enemy, cs, quest_data.version))

    embed_dict['Quest Data'] = [main_embed]
    embed_dict['Enemy Data'] = enemy_embeds
    
    return MixedView(interaction.user, embed_dict, 'Quest Data')

async def tower_view(interaction: Interaction, tower_data: schemas.APIResponse[schemas.Tower], cs: schemas.CommonStrings)->MixedView:
    embed_dict = {}
    tower = tower_data.data
    fixed_rewards = tower.fixed_rewards
    first_time_rewards = tower.first_rewards

    description = StringIO()

    main_embed = BaseEmbed(
        tower_data.version,
        title=f"Tower of {enums.TowerType(tower.tower_type).name} - Floor {tower.floor}",
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
        enemy_embeds.append(detailed_enemy_embed(enemy, cs, tower_data.version))

    embed_dict['Tower Data'] = [main_embed]
    embed_dict['Enemy Data'] = enemy_embeds
    
    return MixedView(interaction.user, embed_dict, 'Tower Data')

