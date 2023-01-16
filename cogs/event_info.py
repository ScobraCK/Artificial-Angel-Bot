import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional, Iterator, Dict

from my_view import My_View
import events
import mission as msn
import common
from master_data import MasterData

def get_utc(diff: int):
    if diff > 0:
        return f"(UTC+{diff})"
    else:
        return f"(UTC{diff})"

def event_mission_texts(missions: Iterator[msn.Mission]):
    texts = []
    batch_it = msn.batched(missions, 7)  # batch into 7 missions
    for i, batch in enumerate(batch_it):
        texts.append('')  # new field
        for mission in batch:
            texts[i] += f"{mission}\n\n"

    return texts
    

def ongoing_event_embed(event_list: List[events.MM_Event]):
    embed = discord.Embed(
        title='Ongoing Events'
    )

    for mm_event in event_list:
        if mm_event.is_ongoing():
            embed.add_field(
                name=mm_event.name,
                value=f"Date: {mm_event.start} ~ {mm_event.end} {get_utc(mm_event.utc_diff)}",
                inline=False
            )

    return embed

def event_detail_embed(mm_event: events.MM_Event, master: MasterData, lang):
    # basic
    text=f"**Start Date**: {mm_event.start} {get_utc(mm_event.utc_diff)}\n\
        **End Date**: {mm_event.end} {get_utc(mm_event.utc_diff)}\n"
    # force start
    if mm_event.has_force_start:
        text += f"**Force Start Date**: {mm_event.force_start} {get_utc(mm_event.utc_diff)}\n"
    
    embed = discord.Embed(
        title=mm_event.name,
        description=text
    )
    field_values: List[Dict[str, str]] = []  # name and value

    # missions
    if mm_event.has_mission:
        mission_it = msn.get_Missions(mm_event.mission_list, master, lang)
        for text in event_mission_texts(mission_it):
            field_values.append(
                {'name': 'Mission List',
                'value': text}
            )

        embed.add_field(**field_values[0])  # show first

    return embed, field_values


class Event_View(My_View):
    def __init__(
        self, user: discord.User, ongoing_embed:discord.Embed, 
        options:List[discord.SelectOption], event_list: List[events.MM_Event],
        master: MasterData, lang: str):

        super().__init__(user)
        self.ongoing_embed = ongoing_embed
        self.embed = ongoing_embed  # current showing embed
        self.event_menu.options=options
        self.event_list = event_list
        self.master = master
        self.lang = lang

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

    @discord.ui.button(label=">", disabled=True)
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
        if value == 'Ongoing Events':
            self.embed = self.ongoing_embed
            self.current_page = 1
            self.max_page = 1
        else: # value is index of event_list
            self.embed, self.fields = event_detail_embed(self.event_list[int(value)], self.master, self.lang) 
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
    language='Language (default: English)',
    server='Game Server (default: NA)'
    )
    async def events(
        self, interaction: discord.Interaction,
        language: Optional[common.Language]=common.Language.English,
        server: Optional[common.Timezone]=common.Timezone.NA):
        '''Shows ongoing event info'''
        event_list = events.get_all_events(self.bot.masterdata, language.value, server)  # ongoing event list

        embed = ongoing_event_embed(event_list)
        options = [discord.SelectOption(
            label='Ongoing Events'
        )]

        for i, mm_event in enumerate(event_list):  
            options.append(discord.SelectOption(
                label=f"{mm_event.name}",
                value=str(i)
            ))
        
        user = interaction.user
        view = Event_View(user, embed, options, event_list, self.bot.masterdata, language.value)
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message


async def setup(bot):
	await bot.add_cog(Event_Commands(bot))