import discord
from discord import app_commands
from discord.ext import commands
from functools import wraps
from typing import List, Optional
from io import StringIO
from itertools import batched
import html2text
import re

from main import AABot
import common
import character as chars
import skill
import equipment
from master_data import MasterData
from pagination import ButtonView, DropdownView, MixedView, show_view
import emoji
from helper import remove_linebreaks

# decorator for char id check
def check_id():
    def decorator(func):
        @wraps(func)
        async def wrapper(_, interaction: discord.Interaction, *args, **kwargs):
            character = kwargs.get('character', None) or args[0]
            if not chars.check_id(character):
                await interaction.response.send_message(
                    f"A character id of `{character}` does not exist.",
                    ephemeral=True
                )
                return
            return await func(_, interaction, *args, **kwargs)
        return wrapper
    return decorator

# transformer for id
class IdTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> int:
        try:
            id = int(value)
        except ValueError:
            id = chars.find_id_from_name(value)
        return id
    
    
#########################
# character
#########################

def dict_to_embedtext(data: dict, whitelist: List)->str:
    text = ''
    for key in data:
        if key in whitelist:
            text = text + f'**{key}:** {data[key]}\n'

    return text

def active_name_text(char, master: MasterData, lang=None):
    # returns skill name and cd
    text=''
    for active_skill in skill.skill_info(
        char, common.Skill_Enum.Active, master, descriptions=False, lang=lang):
        text += f"{active_skill['Name']} **CD:** {active_skill['Cooldown']}\n"
    return text

def passive_name_text(char, master: MasterData, lang=None):
    # returns passive skill name
    if char['Passive Skills']:
        text=''
        for passive_skill in skill.skill_info(
            char, common.Skill_Enum.Passive, master, descriptions=False, lang=lang):
            text += f"{passive_skill['Name']}\n"
        return text
    else:
        return 'None'

def uw_text(uw_description):
    if uw_description is None:
        return 'None'
    text=''
    for rarity in common.uw_rarity_list:
        text += f"__**{rarity} Weapon**__{emoji.rarity_emoji.get(rarity)}\n{uw_description.get(rarity)}\n"

    return text

def char_info_embed(id: int, masterdata: MasterData, lang=None)->discord.Embed:
    '''
    embed with basic character info
    '''
    char = chars.get_character_info(id, masterdata, lang=lang)

    if not char:  # TEMP
        return discord.Embed(description='Character data invalid.', )

    name = f'{char["Name"]}'
    if char['Title']:
        name = f'[{char["Title"]}] ' + name
    embed = discord.Embed(
        title=name,
        description=dict_to_embedtext(char, common.basic_info))

    # active skill
    embed.add_field(
        name='__Active Skills__',
        value=active_name_text(char, masterdata, lang=lang),
        inline=False
    )
    # passive skills
    embed.add_field(
        name='__Passive Skills__',
        value=passive_name_text(char, masterdata, lang=lang),
        inline=False
    )
    # thumbnail
    image_link = common.raw_asset_link_header + f'Characters/Sprites/CHR_{char["Id"]:06}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

#########################
# skill
#########################

def skill_level_embeds(skill: dict, type: common.Skill_Enum, embed:discord.Embed) -> dict:
    '''
    adds embed field for skill levels
    '''
    title_text = f"**{skill['Name']}**"
    if type is common.Skill_Enum.Active:  # for actives
        title_text += f' | **CD:** {skill["Cooldown"]}'

    embed.add_field(name='\u200b', value=title_text, inline=False)

    text = ''
    for i, description in enumerate(skill['Descriptions'], 1):
        unlock_lv = f"Lv.{description['Lv']}"
        embed.add_field(
            name=f"__**Skill Lv.{i}**__{emoji.level_emoji.get(i)} ({unlock_lv})",
            value=remove_linebreaks(description['Description']),
            inline=False
        )

def skill_embed(char: dict, type: common.Skill_Enum, masterdata: MasterData, lang=None):
    '''
    Embed for skills, active or passive
    '''
    embed = discord.Embed(
        title=f"{char['Name']}'s Skills",
        description=f"__**{masterdata.search_string_key(type.value)}**__",)

    for skill_description in skill.skill_info(char, type, master=masterdata, lang=lang):
        skill_level_embeds(skill_description, type, embed)
        
    if type is common.Skill_Enum.Passive and \
        not char['Passive Skills']:  # 'Passive Skills'
        embed.add_field(name='None', value='\u200b', inline=False)

    # thumbnail
    image_link = common.raw_asset_link_header + f'Characters/Sprites/CHR_{char["Id"]:06}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

def uw_skill_embed(char: dict, masterdata: MasterData, lang=None):
    '''
    Embed for only the skill descriptions of UW
    '''
    embed = discord.Embed(
        title=f"{char['Name']}'s Skills",
        description=f"__**Unique Weapon Effects**__")

    uw_description = equipment.get_uw_descriptions(char['Id'], masterdata, lang=lang)
    embed.add_field(name='\u200b', value=remove_linebreaks(uw_text(uw_description)), inline=False)

    # thumbnail
    image_link = common.raw_asset_link_header + f'Characters/Sprites/CHR_{char["Id"]:06}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

#########################
# skill detail (skill revamp)
#########################

def subskill_embed(subskill: skill.Subskill, type: common.Skill_Enum, embed: discord.Embed)->None:
    '''helper function to modify embed for subset skills'''
    # common field
    embed.add_field(
        name='Details',
        value=(
        f"```json\n"
        f"Order Number: {subskill.skill_level}\n"
        f"Character Level: {subskill.unlock_level}\n"
        f"Equipment Rarity: {subskill.uw_rarity if subskill.uw_rarity else 'None'}```"
        ),
        inline=False
    )
    if type is common.Skill_Enum.Active:
        active_subset_text = '\n'.join(map(str, subskill.subsetskills))
        embed.add_field(
            name='Sub Set Skills',
            value=f"```json\n{active_subset_text}```",
            inline=False
        )
    else:  # passives
        passive_subset_text=''
        for subset in subskill.subsetskills:
            passive_subset_text += (
                f"```json\n"
                f"Passive Trigger: {subset.get('PassiveTrigger')}\n"
                f"Initial CD: {subset.get('SkillCoolTime')}\n"
                f"Max CD: {subset.get('SkillMaxCoolTime')}\n"
                f"Sub Set Skill Id: {subset.get('SubSetSkillId')}```"
                )
            
        embed.add_field(
            name='Sub Set Skills',
            value=passive_subset_text,
            inline=False
        )
        

def skill_detail_embeds(skill_info: skill.Skill, master: MasterData, lang) -> List[discord.Embed]:
    icon_url = common.raw_asset_link_header + f"Characters/Skills/{skill_info.icon}"

    description = f"__{skill_info.type_name}__\n"
    
    if skill_info.type is common.Skill_Enum.Active:
        description += f"**CD: ** {skill_info.max_cd}"

    embed = discord.Embed(
        title=f"{skill_info.name}",
        description= description,
        color=discord.Colour.blue()
    )
    detail_embeds = []  # for subskill details
    for subskill in skill_info.subskills:
        # main embed
        if not subskill.uw_rarity: # Normal unlock skill
            name = f"__**Skill Lv.{subskill.skill_level}**__{subskill.emoji} (Lv.{subskill.unlock_level})"
        else:  # UW skill 
            name = f"__{subskill.uw_rarity} Unique Weapon__{subskill.emoji}"
        embed.add_field(
            name=name,
            value=remove_linebreaks(subskill.description),
            inline=False)
        
        # detail embed
        detail_embed = discord.Embed(
            title=f"{skill_info.name}",
            description=remove_linebreaks(subskill.description),
            color=discord.Colour.blue())
        
        if skill_info.type is common.Skill_Enum.Active: 
            # cooldown info for active only
            detail_embed.add_field(
                name='Cooldown Info',
                value=f"```json\nInit CD: {skill_info.init_cd}\nMax CD: {skill_info.max_cd}```",
                inline=False
            )
        subskill_embed(subskill, skill_info.type, detail_embed)
        detail_embed.set_thumbnail(url=icon_url)
        detail_embeds.append(detail_embed)

    embed.set_thumbnail(url=icon_url)

    return [embed] + detail_embeds


# character cog
class Character(commands.Cog, name='Character Commands'):
    '''These are helpful tip commands'''

    def __init__(self, bot):
        self.bot: AABot = bot

    @app_commands.command()
    @app_commands.describe(
    language='Language to show character names. Defaults to English.'
    )
    async def idlist(
        self, 
        interaction: discord.Interaction,
        language: Optional[common.Language]=common.Language.EnUs):
        '''
        Shows character ids
        '''
        embeds = []
        for batch in batched(common.id_list.keys(), 20):
            text = StringIO()
            for id in batch:
                text.write(f"{id}: {chars.get_full_name(id, self.bot.masterdata, language)}\n")
            embed = discord.Embed(
                title='Character Id',
                color=discord.Color.green(),
                description=text.getvalue()
                )
            embeds.append(embed)
        
        user=interaction.user
        view = ButtonView(user, {'default': embeds})
        await show_view(interaction, view)
    
    @app_commands.command()
    @app_commands.describe(
    character='The name or id of the character',
    language='Text language. Defaults to English.'
    )
    @check_id()
    async def character(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer], # is an id
        language: Optional[common.Language]=common.Language.EnUs):  
        '''Shows a character's basic info'''

        embed = char_info_embed(character, self.bot.masterdata, lang=language)

        if not embed.title:  #TEMP
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @check_id()
    async def skill(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: Optional[common.Language]=common.Language.EnUs):
        '''Shows character skills including unique weapon upgrade effects'''

        char = chars.get_character_info(character, self.bot.masterdata, lang=language)
        if not char:  # TEMP
            embed = discord.Embed(description='Character data invalid.')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed_dict = {
            'Active': [skill_embed(char, common.Skill_Enum.Active, self.bot.masterdata, lang=language)],
            'Passive': [skill_embed(char, common.Skill_Enum.Passive, self.bot.masterdata, lang=language)],
            'Unique Weapon': [uw_skill_embed(char, self.bot.masterdata, lang=language)]
        }
            
        user = interaction.user
        view = DropdownView(user, embed_dict, key='Active')
        await show_view(interaction, view)

    @app_commands.command()
    @app_commands.describe(
        add='Additional speed from speed runes',
        buffs='List of speed buff percentages',
    )
    async def speed(self, interaction: discord.Interaction, add: Optional[int]=0, buffs: Optional[str]=None):
        '''List character speeds in decreasing order'''
        speed_dict = chars.speed_sorted(self.bot.masterdata)
        embed_dict = {}
        
        if buffs is None:
            buff_list = [0]
        else:
            try:
                buff_list = [0] + [int(buff) for buff in re.split(r'[,\s]+', buffs) if buff]
            except ValueError:
                await interaction.response.send_message(
                    "Invalid input for buffs. Please enter a list of integers separated by commas or spaces. Example /speed `-15 15 30`", 
                    ephemeral=True
                    )
                return
            
        for buff in buff_list:
            i = 1
            embeds = []
            for batch in batched(speed_dict.items(), 20):
                text = StringIO()
                for id, speed in batch:
                    text.write(f"**{i}.** {common.id_list[id]} {int((speed+add)*(1+buff/100))}\n")
                    i += 1
                embed = discord.Embed(
                    title='Character Speeds',
                    description=text.getvalue(),
                    color=discord.Colour.orange())
                if add != 0 or buff != 0:
                    embed.add_field(
                        name='Bonus Parameters',
                        value=f'Rune Bonus: {add}\nBuffs: {buff}%',
                        inline=False
                    )
                embeds.append(embed)
            if buff == 0:
                embed_dict['Base Speed'] = embeds
            else:
                embed_dict[f'{buff}% Speed'] = embeds
                

        user = interaction.user
        view = MixedView(user, embed_dict, 'Base Speed')
        await show_view(interaction, view)

    
    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @check_id()
    async def skilldetails(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: Optional[common.Language]=common.Language.EnUs):
        '''Shows character skills and details'''

        skill_list = skill.skill_detail_info(character, self.bot.masterdata, language)

        embed_dict = {}
        default_key = None
        for skill_info in skill_list:
            if default_key == None:
                default_key = skill_info.name
            embed_dict[skill_info.name] = skill_detail_embeds(skill_info, self.bot.masterdata, language)  
            
        user = interaction.user
        view = MixedView(user, embed_dict, default_key)
        await show_view(interaction, view)
            
    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @check_id()
    async def voicelines(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: Optional[common.Language]=common.Language.EnUs):
        '''Shows character voicelines'''
        voicelines = chars.get_voicelines(character, self.bot.masterdata, language)
        # f'{common.moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{}'
        
        name = chars.get_full_name(character, self.bot.masterdata, lang=language)
        embeds = []
        h = html2text.HTML2Text()
        
        for batch in batched(voicelines.items(), 6):
            embed = discord.Embed(title=f"{name}'s Voicelines", color=discord.Color.gold())
            for key, text in batch:
                embed.add_field(name=key, value=h.handle(text), inline=False)
            embeds.append(embed)
        
        user = interaction.user
        view = ButtonView(user, {'default': embeds})
        await show_view(interaction, view)
        
    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    @check_id()
    async def memories(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: Optional[common.Language]=common.Language.EnUs):
        '''Shows character memories'''
        memories = chars.get_memories(character, self.bot.masterdata, language)
        # f'{common.moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{:06}'
        
        name = chars.get_full_name(character, self.bot.masterdata, lang=language)
        embeds = []
        h = html2text.HTML2Text()
        for i, (k, text) in enumerate(memories.items(), 1):
            text = f'**{k}**\n{h.handle(text)}'
            embed = discord.Embed(title=f"{name}'s Memories", description=text,color=discord.Color.dark_gold())
            
            # assets
            jp_url = f'{common.moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{character:06}/Memory/MEM_{i:06}'
            us_url = f'{common.moonheart_assets}/AddressableConvertAssets/Voice/US/Character/CHR_{character:06}/Memory/MEM_{i:06}'
            embed.add_field(name='Voice',value=f'[JP]({jp_url})|[US]({us_url})', inline=False)
            embeds.append(embed)
        
        user = interaction.user
        view = ButtonView(user, {'default': embeds})
        await show_view(interaction, view)
        

async def setup(bot):
	await bot.add_cog(Character(bot))