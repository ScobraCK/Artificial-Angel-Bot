import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional, Iterator, Dict, Tuple
from itertools import batched

from pagination import MyView
import events as evt
import mission as msn
from common import Language, Server

from master_data import MasterData

def event_mission_texts(missions: Iterator[msn.Mission])->List[str]:
    texts = []
    for i, batch in enumerate(batched(missions, 7)):
        texts.append('')  # new field
        for mission in batch:
            texts[i] += f"{mission}\n\n"
            
    return texts
    

def event_list_embed(event_list: List[evt.MM_Event], server: str):
    embed = discord.Embed(
        title='Event List',
        description=f"**Server:** {server}"
    )
    past_text = ''
    ongoing_text = ''
    future_text = ''
    for mm_event in event_list:
        state = mm_event.state()
        if state == 0:
            ongoing_text += (
                f"{mm_event.type_indication}**{mm_event.name}**\n"
                f"Date: <t:{mm_event.start}> ~ <t:{mm_event.end}>\n"
            )
        elif state > 0:
            future_text += (
                f"{mm_event.type_indication}**{mm_event.name}**\n"
                f"Date: <t:{mm_event.start}> ~ <t:{mm_event.end}>\n"
            )
        else:
            past_text += (
                f"{mm_event.type_indication}**{mm_event.name}**\n"
                f"Date: <t:{mm_event.start}> ~ <t:{mm_event.end}>\n"
            )

    if past_text:
        embed.add_field(
            name='__Past Events__',
            value=past_text,
            inline=False
        )

    embed.add_field(
        name='__Ongoing Events__',
        value= (ongoing_text if ongoing_text else "None"),
        inline=False
    )
    embed.add_field(
        name='__Future Events__',
        value= (future_text if future_text else "None"),
        inline=False
    )

    return embed

def event_detail_embed(mm_event: evt.MM_Event, master: MasterData, lang):
    # basic
    text=(
        f"**Server:** {mm_event.server.name}\n"
        f"**Start Date:** <t:{mm_event.start}>\n"
        f"**End Date:** <t:{mm_event.end}>\n"
    )
    # force start
    if mm_event.has_force_start:
        text += f"**Force Start Date:** <t:{mm_event.force_start}>\n"
    # ingame descriptions
    if (desc := mm_event.description):
        text += f"\n{desc}\n"
    
    embed = discord.Embed(
        title=mm_event.name,
        description=text
    )
    field_values: List[Dict[str, str]] = []  # name and value for embed

    # missions
    if mm_event.has_mission:
        char_name = None
        if isinstance(mm_event, evt.NewCharacter):
            char_name = mm_event.character

        mission_it = msn.get_Missions(mm_event.mission_list, master, lang)
        for mission_text in event_mission_texts(mission_it):
            if char_name:
                mission_text.replace('{0}', char_name)
            field_values.append(
                {'name': '__Mission List__',
                'value': mission_text}
            )

    if isinstance(mm_event, evt.BountyQuest): #Bounty Quests
        item_text = f"**Bonus Multiplier:** {mm_event.multiplier}%\n\n"
        for item in mm_event.targets:
            item_text += f"**-{item}**\n"
        field_values.append(
            {'name': '__Target Items__',
             'value': item_text}
        )

    embed.add_field(**field_values[0])  # show first

    return embed, field_values


class Event_View(MyView):
    def __init__(
        self, user: discord.User, main_embed:discord.Embed, 
        options:List[discord.SelectOption], event_embeds: Dict[str, Tuple[discord.Embed, List[str]]]):

        super().__init__(user)
        self.main_embed = main_embed
        self.embed = main_embed  # current showing embed
        self.event_menu.options=options
        self.event_embeds = event_embeds

        self.fields = None
        self.current_page = 1
        self.max_page = 1

    async def btn_update(self):
        if self.current_page == 1:
            self.left2_btn.disabled = True
            self.left_btn.disabled = True
        else:
            self.left2_btn.disabled = False
            self.left_btn.disabled = False

        if self.current_page == self.max_page:
            self.right_btn.disabled = True
            self.right2_btn.disabled = True
        else:
            self.right_btn.disabled = False
            self.right2_btn.disabled = False

        self.mid_btn.label = f"{self.current_page}/{self.max_page}"

    @discord.ui.button(label="<<", disabled=True)
    async def left2_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += -10
        if self.current_page < 1:
            self.current_page = 1
        self.embed.set_field_at(0, **self.fields[self.current_page-1])
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="<", disabled=True)
    async def left_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += -1
        self.embed.set_field_at(0, **self.fields[self.current_page-1])
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="1/1", disabled=True)
    async def mid_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=">", disabled=True)
    async def right_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.embed.set_field_at(0, **self.fields[self.current_page-1])
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label=">>", disabled=True)
    async def right2_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 10
        if self.current_page > self.max_page:
            self.current_page = self.max_page
        self.embed.set_field_at(0, **self.fields[self.current_page-1])
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.select()
    async def event_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        value = select.values[0]
        if value == 'Event List':  # see event command
            self.embed = self.main_embed
            self.current_page = 1
            self.max_page = 1
        else: # value is index of event_list
            self.embed = self.event_embeds.get(value)[0]
            self.fields = self.event_embeds.get(value)[1]
            self.max_page = len(self.fields)
            self.current_page = 1
            
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

class Event_Commands(commands.Cog, name='Event Commands'):
    '''Commands for game events'''

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
    language='Text language. Defaults to English.',
    server='Game server to calculate the timezone. Defaults to NA.'
    )
    async def events(
        self, interaction: discord.Interaction,
        language: Optional[Language]=Language.EnUs,
        server: Optional[Server]=Server.America):
        '''Shows ongoing and future event info'''
        event_list = evt.get_all_events(self.bot.masterdata, language.value, server)

        main_embed = event_list_embed(event_list, server.name)
        options = [discord.SelectOption(
            label='Event List'
        )]
        event_embeds = {}

        await interaction.response.defer()

        for mm_event in event_list:  
            options.append(discord.SelectOption(
                label=f"{mm_event.name}"
            ))
            # {event name: (embed, fields)}
            event_embeds[mm_event.name] = event_detail_embed(
                mm_event, self.bot.masterdata, language.value)
            
        
        user = interaction.user
        view = Event_View(user, main_embed, options, event_embeds)
        await interaction.followup.send(embed=main_embed, view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Event_Commands(bot))