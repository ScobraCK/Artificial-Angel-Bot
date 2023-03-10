import discord
from discord import app_commands
from discord.ext import commands
from typing import Iterable, List, Optional, Tuple, Dict

import common
import character as chars
import skill
import equipment
from master_data import MasterData
from my_view import My_View, Button_View
import emoji

#########################
# idlist
#########################
def id_list_embed():
    text = ''
    id_list = common.id_list
    
    embed = discord.Embed(
        title='Character Id'
    )
    for i in range(1, common.MAX_CHAR_ID+1, 20):
        text=''
        for j in range(i, i+20):
            if j > common.MAX_CHAR_ID:
                break
            text += f"{j}. {id_list[j]}\n"
        embed.add_field(name='\u200b', value=text)

    return embed

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
    name = f'{char["Name"]}'
    if char['Title']:
        name = name + f' [{char["Title"]}]'
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

class Skill_View(My_View):
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

def speed_text(master: MasterData, max: int=20) -> Tuple[str, List]:
    '''
    get first 20(max) characters and also returns the speed iter
    '''
    speed_it = chars.speed_iter(master)
    text = ''
    try:
        for i in range(1, max+1):
            speed = next(speed_it)
            text += f"**{i}.** {common.id_list[speed[0]]} {speed[1]}\n"
    except StopIteration:
        pass

    return text, speed_it


class Speed_View(My_View):
    def __init__(self, user: discord.User, embed: discord.Embed, speed_it: Iterable):
        super().__init__(user)
        self.it = speed_it
        self.embed = embed
        
    @discord.ui.button(label="Show All")
    async def btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled=True
        text = ''
        for i, speed in enumerate(self.it, 21):  # 20 is already shown
            text += f"**{i}.** {common.id_list[speed[0]]} {speed[1]}\n"
        self.embed.description += text
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

class Skill_Detail_View(Button_View):
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
        self.bot = bot

    @app_commands.command()
    async def idlist(self, interaction: discord.Interaction):
        '''
        Shows character ids
        '''
        embed = id_list_embed()

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command()
    @app_commands.describe(
    character='The name or id of the character',
    language='Text language. Defaults to English.'
    )
    async def character(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer], # is an id
        language: Optional[common.Language]=common.Language.English):  
        '''Shows a character's basic info'''
        if not chars.check_id(character):
            await interaction.response.send_message(
                f"A character id of `{character}` does not exist.",
                ephemeral=True
            )
        else:
            embed = char_info_embed(character, self.bot.masterdata, lang=language)
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    async def skill(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: Optional[common.Language]=common.Language.English):
        '''Shows character skills including unique weapon upgrade effects'''
        if not chars.check_id(character):
            await interaction.response.send_message(
                f"A character id of `{character}` does not exist.",
                ephemeral=True
            )
        else:
            char = chars.get_character_info(character, self.bot.masterdata, lang=language)

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
        text, speed_it = speed_text(self.bot.masterdata)
        embed = discord.Embed(
            title='Character Speeds',
            description=text)
        user = interaction.user
        view = Speed_View(user, embed, speed_it)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

    
    @app_commands.command()
    @app_commands.describe(
        character='The name or id of the character',
        language='Text language. Defaults to English.'
    )
    async def skilldetails(
        self,
        interaction: discord.Interaction,
        character: app_commands.Transform[int, IdTransformer],
        language: Optional[common.Language]=common.Language.English):
        '''Shows character skills and details'''
        if not chars.check_id(character):
            await interaction.response.send_message(
                f"A character id of `{character}` does not exist.",
                ephemeral=True
            )
        else:

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


async def setup(bot):
	await bot.add_cog(Character(bot))