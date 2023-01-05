from typing import List, Optional, Tuple, Iterable
import discord

from master_data import MasterData
import common
import skill
import character
import equipment

###############
# embed texts
###############

def dict_to_embedtext(data: dict, whitelist: List)->str:
    text = ''
    for key in data:
        if key in whitelist:
            text = text + f'**{key}**: {data[key]}\n'

    return text

def active_name_text(char, masterdata: MasterData):
    # returns skill name and cd
    text=''
    for active_skill in skill.skill_info(char, common.Skill_Enum.ACTIVE, descriptions=False, masterdata=masterdata):
        text = text + f"{active_skill['Name']} **CD:** {active_skill['Cooldown']}\n"
    return text

def passive_name_text(char, masterdata: MasterData):
    # returns passive skill name
    if char[common.Skill_Enum.PASSIVE.value]:
        text=''
        for passive_skill in skill.skill_info(char, common.Skill_Enum.PASSIVE, descriptions=False, masterdata=masterdata):
            text = text + f"{passive_skill['Name']}\n"
        return text
    else:
        return 'None'

def uw_text(uw_description):
    if uw_description is None:
        return 'None'
    text=''
    for rarity in common.uw_rarity_list:
        text += f"__**{rarity} Weapon**__{common.rarity_emoji.get(rarity)}\n{uw_description.get(rarity)}\n"

    return text

def speed_text(masterdata, max: int=20) -> Tuple[str, List]:
    '''
    get first 20(max) characters and also returns the speed iter
    '''
    speed_it = character.speed_iter(masterdata)
    text = ''
    try:
        for i in range(1, max+1):
            speed = next(speed_it)
            text += f"**{i}.** {common.id_list[speed[0]]} {speed[1]}\n"
    except StopIteration:
        pass

    return text, speed_it

###############
# Views
###############
class My_View(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=180)
        self.user=user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        check = (interaction.user.id == self.user.id)
        if not check:
            await interaction.response.send_message(
                'Only the original command user can change this',
                ephemeral=True
            )
        return check

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

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

###############
# embeds
###############

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

def char_info_embed(id: int, masterdata: MasterData)->discord.Embed:
    '''
    embed with basic character info
    '''
    char = character.get_character_info(id, masterdata)
    name = f'{char["Name"]}'
    if char['Title']:
        name = name + f' [{char["Title"]}]'
    embed = discord.Embed(
        title=name,
        description=dict_to_embedtext(char, common.basic_info))

    # active skill
    embed.add_field(
        name='__Active Skills__',
        value=active_name_text(char, masterdata),
        inline=False
    )
    # passive skills
    embed.add_field(
        name='__Passive Skills__',
        value=passive_name_text(char, masterdata),
        inline=False
    )
    # thumbnail
    image_link = common.raw_asset_link_header + f'/CHR_000{char["Id"]:03}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

def skill_level_embeds(skill: dict, type: common.Skill_Enum, embed:discord.Embed) -> dict:
    '''
    adds embed field for skill levels
    '''
    title_text = f"**{skill['Name']}**"
    if type is common.Skill_Enum.ACTIVE:  # for actives
        title_text += f' | **CD:** {skill["Cooldown"]}'

    embed.add_field(name='\u200b', value=title_text, inline=False)

    text = ''
    for i, description in enumerate(skill['Descriptions'], 1):
        unlock_lv = f"Lv.{description['Lv']}"
        embed.add_field(
            name=f"__**Skill Lv.{i}**__{common.level_emoji.get(i)} ({unlock_lv})",
            value=description['Description'],
            inline=False
        )

def skill_embed(char: dict, type: common.Skill_Enum, masterdata: MasterData):
    '''
    Embed for skills, active or passive
    '''
    embed = discord.Embed(
        title=f"{char['Name']}'s Skills",
        description=f"__**{type.value}**__")

    for skill_description in skill.skill_info(char, type, masterdata=masterdata):
        skill_level_embeds(skill_description, type, embed)
        
    if type is common.Skill_Enum.PASSIVE and \
        not char[common.Skill_Enum.PASSIVE.value]:  # 'Passive Skills'
        embed.add_field(name='None', value='\u200b', inline=False)

    # thumbnail
    image_link = common.raw_asset_link_header + f'/CHR_000{char["Id"]:03}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

def uw_skill_embed(char: dict, masterdata: MasterData):
    '''
    Embed for only the skill descriptions of UW
    '''
    embed = discord.Embed(
        title=f"{char['Name']}'s Skills",
        description=f"__**Unique Weapon Effects**__")

    uw_description = equipment.get_uw_descriptions(char['Id'], masterdata)
    embed.add_field(name='\u200b', value=uw_text(uw_description), inline=False)

    # thumbnail
    image_link = common.raw_asset_link_header + f'/CHR_000{char["Id"]:03}_00_s.png'
    embed.set_thumbnail(url=image_link)

    return embed

#testing
if __name__ == "__main__":
    text, it = speed_text(MasterData())
    print(text)
    print(next(it))
