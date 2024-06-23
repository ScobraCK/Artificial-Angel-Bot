import discord
from discord import app_commands
from discord.ext import commands
from functools import wraps
from typing import Iterable, List, Optional, Tuple, Dict
from io import StringIO
from itertools import batched
import html2text

from main import AABot
import common
import character as chars
import skill
import equipment
from master_data import MasterData
from pagination import MyView, ButtonView, ButtonView2, show_view
import emoji

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


#########################
# idlist
#########################
def id_list_embed(master: MasterData, lang: Optional[common.Language]):
    text = ''
    id_list = common.id_list
    
    text = StringIO()
    max = len(id_list)
    embeds = []
    for i, k in enumerate(id_list.keys(), 1):
        text.write(f"{k}: {chars.get_full_name(k, master, lang)}\n")  # not the most efficient way to get ALL names
        if i % 20 == 0 or i == max:
            embed = discord.Embed(
                title='Character Id',
                color=discord.Color.green(),
                description=text.getvalue()
            )
            embeds.append(embed)
            text = StringIO()

    return embeds

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
    image_link = common.raw_asset_link_header + f'Characters/Sprites/CHR_000{char["Id"]:03}_00_s.png'
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
            value=description['Description'],
            inline=False
        )

def skill_embed(char: dict, type: common.Skill_Enum, masterdata: MasterData, lang=None):
    '''
    Embed for skills, active or passive
    '''
    embed = discord.Embed(
        title=f"{char['Name']}'s Skills",
        description=f"__**{masterdata.search_string_key(type.value)}**__")

    for skill_description in skill.skill_info(char, type, master=masterdata, lang=lang):
        skill_level_embeds(skill_description, type, embed)
        
    if type is common.Skill_Enum.Passive and \
        not char['Passive Skills']:  # 'Passive Skills'
        embed.add_field(name='None', value='\u200b', inline=False)

    # thumbnail
    image_link = common.raw_asset_link_header + f'Characters/Sprites/CHR_000{char["Id"]:03}_00_s.png'
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
    embed.add_field(name='\u200b', value=uw_text(uw_description), inline=False)

    # thumbnail
    image_link = common.raw_asset_link_header + f'Characters/Sprites/CHR_000{char["Id"]:03}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

class Skill_View(MyView):
    def __init__(self, user: discord.User, embeds:List[discord.Embed]):
        super().__init__(user)
        self.embeds = embeds

    async def update_button(self, button: discord.ui.Button):
        for btn in self.children:
            if btn is button:
                btn.disabled=True
            else:
                btn.disabled=False

    @discord.ui.button(label="Active", disabled=True)
    async def active_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[0], view=self)
        
    @discord.ui.button(label="Passive")
    async def passive_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[1], view=self)

    @discord.ui.button(label="Unique Weapon")
    async def uw_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_button(button)
        await interaction.response.edit_message(embed=self.embeds[2], view=self)

#########################
# speed
#########################

#TODO rework to named tuple
def speed_text(speedtuple: Tuple[int, int], buff: int=0) -> Tuple[str, List]:
    '''
    output speed text for single character from speed tuple
    ''' 
    text = f"{common.id_list[speedtuple[0]]} {int(speedtuple[1]*(1+buff/100))}\n"

    return text

def speed_listing(speed_list, count: int ,buff: int=0) -> str:
    '''
    output speed text for multiple characters
    '''
    text = StringIO()
    for i, speed in enumerate(speed_list, 1):
        text.write(f"**{i}.** {speed_text(speed, buff)}")
        if i == count:
            break
    return text.getvalue()


class Speed_View(MyView):
    def __init__(self, user: discord.User, embed: discord.Embed, speed_list: List):
        super().__init__(user)
        self.speed_list = speed_list
        self.embed = embed
        self.showall = False
        self.count = 20 # current view state (not button state)
        self.buff = 0

    @discord.ui.button(label="Default")
    async def default_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.buff = 0
        self.embed.description = speed_listing(self.speed_list, self.count, self.buff)
        await interaction.response.edit_message(embed=self.embed, view=self)
       
    @discord.ui.button(label="10%")
    async def btn10(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.buff = 10
        self.embed.description = speed_listing(self.speed_list, self.count, self.buff)
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="15%")
    async def btn15(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.buff = 15
        self.embed.description = speed_listing(self.speed_list, self.count, self.buff)
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Show All", row=2)
    async def show_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.showall:
            self.showall = False
            button.label = "Show All"
            self.count = 20
        else:
            self.showall = True
            button.label = "Show Less"
            self.count = 0  # 0 count shows all
        
        self.embed.description = speed_listing(self.speed_list, self.count, self.buff)
        await interaction.response.edit_message(embed=self.embed, view=self)

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
            value=subskill.description,
            inline=False)
        
        # detail embed
        detail_embed = discord.Embed(
            title=f"{skill_info.name}",
            description=subskill.description,
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

class Skill_Detail_View(ButtonView):
    def __init__(self, user: discord.User, embeds: List[discord.Embed],
                 skills: Dict[str, skill.Skill], options: List[discord.SelectOption],
                 master: MasterData, lang: common.Language):
        super().__init__(user, embeds)
        self.skills = skills
        self.skill_menu.options = options
        self.master = master
        self.lang = lang

    @discord.ui.select()
    async def skill_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        value = select.values[0]
        self.embeds = skill_detail_embeds(self.skills.get(value), self.master, self.lang)
        self.max_page = len(self.embeds)
        self.current_page = 1
        self.embed = self.embeds[0]

        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)


# transformer for id
class IdTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> int:
        try:
            id = int(value)
        except ValueError:
            id = chars.find_id_from_name(value)
        return id

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
        embeds = id_list_embed(self.bot.masterdata, language)
        user = interaction.user
        view = ButtonView(user, embeds)
        await view.btn_update()

        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message

    
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
        embeds = [
            skill_embed(char, common.Skill_Enum.Active, self.bot.masterdata, lang=language),
            skill_embed(char, common.Skill_Enum.Passive, self.bot.masterdata, lang=language),
            uw_skill_embed(char, self.bot.masterdata, lang=language)
        ]
        user = interaction.user
        view = Skill_View(user, embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message

    @app_commands.command()
    async def speed(self, interaction: discord.Interaction):
        '''List character speeds in decreasing order'''
        speed_list = list(chars.speed_iter(self.bot.masterdata))

        embed = discord.Embed(
            title='Character Speeds',
            description=speed_listing(speed_list, 20),
            color=discord.Colour.orange())
        
        user = interaction.user
        view = Speed_View(user, embed, speed_list)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

    
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

        skill_dict = {}
        options = []
        for skill_info in skill_list:
            options.append(discord.SelectOption(label=skill_info.name))
            skill_dict[skill_info.name] = skill_info

        embeds = skill_detail_embeds(skill_list[0], self.bot.masterdata, language)  #initial S1 embed
        user = interaction.user
        view = Skill_Detail_View(user, embeds, skill_dict, options, self.bot.masterdata, language)
        await view.btn_update()

        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message
            
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
        voicelines = chars.get_voicelines(character, self.bot.masterdata)
        # f'{common.moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{}'
        
        name = chars.get_full_name(character, self.bot.masterdata, lang=language)
        embeds = []
        for batch in batched(voicelines.items(), 6):
            embed = discord.Embed(title=f"{name}'s Voicelines", color=discord.Color.gold())
            for key, text in batch:
                embed.add_field(name=key, value=text, inline=False)
            embeds.append(embed)
        
        user = interaction.user
        view = ButtonView2(user, {'default': embeds})
        await show_view(interaction, view, embeds[0])
        
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
        memories = chars.get_memories(character, self.bot.masterdata)
        # f'{common.moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{:06}'
        
        name = chars.get_full_name(character, self.bot.masterdata, lang=language)
        embeds = []
        h = html2text.HTML2Text()
        for i, (k, text) in enumerate(memories.items(), 1):
            embed = discord.Embed(title=f"{name}'s Memories", color=discord.Color.dark_gold())
            embed.add_field(name=k, value=h.handle(text), inline=False)
            
            # assets
            jp_url = f'{common.moonheart_assets}/AddressableConvertAssets/Voice/JP/Character/CHR_{character:06}/Memory/MEM_{i:06}'
            us_url = f'{common.moonheart_assets}/AddressableConvertAssets/Voice/US/Character/CHR_{character:06}/Memory/MEM_{i:06}'
            embed.add_field(name='Voice',value=f'[JP]({jp_url})|[US]({us_url})', inline=False)
            embeds.append(embed)
        
        user = interaction.user
        view = ButtonView2(user, {'default': embeds})
        await show_view(interaction, view, embeds[0])
        

async def setup(bot):
	await bot.add_cog(Character(bot))