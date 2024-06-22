from datetime import datetime
from typing import Any, List
import discord

class MyView(discord.ui.View):
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
    
    async def update(self):
        pass

class ButtonView(MyView):
    def __init__(self, user: discord.User, embeds: List[discord.Embed]):
        super().__init__(user)
        self.current_page = 1
        self.max_page=len(embeds)
        self.embeds = embeds
        self.embed = embeds[0]
        self.mid_btn.label = f'1/{self.max_page}'

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
        self.embed =self.embeds[self.current_page-1]
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="<", disabled=True)
    async def left_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += -1
        self.embed =self.embeds[self.current_page-1]
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="1/1", disabled=True)
    async def mid_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=">", disabled=True)
    async def right_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.embed =self.embeds[self.current_page-1]
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label=">>", disabled=True)
    async def right2_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 10
        if self.current_page > self.max_page:
            self.current_page = self.max_page
        self.embed =self.embeds[self.current_page-1]
        await self.btn_update()
        await interaction.response.edit_message(embed=self.embed, view=self)

class ButtonView2(MyView):
    def __init__(self, user: discord.User, embeds_dict: dict[str, List[discord.Embed]], default_key='default'):
        super().__init__(user)
        self.current_page = 1
        self.embed_dict = embeds_dict
        self.embeds = self.embed_dict.get(default_key)
        self.max_page=len(self.embeds)
        self.embed = self.embeds[0]
        self.mid_btn.label = f'1/{self.max_page}'
        
    def change_embed(self, key):
        self.current_page = 1
        self.embeds = self.embeds_dict.get(key)
        self.max_page=len(self.embeds)
        self.embed = self.embeds[0]
        self.mid_btn.label = f'1/{self.max_page}'

    async def update(self):
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
        self.embed =self.embeds[self.current_page-1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="<", disabled=True)
    async def left_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += -1
        self.embed =self.embeds[self.current_page-1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="1/1", disabled=True)
    async def mid_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=">", disabled=True)
    async def right_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.embed =self.embeds[self.current_page-1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label=">>", disabled=True)
    async def right2_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 10
        if self.current_page > self.max_page:
            self.current_page = self.max_page
        self.embed =self.embeds[self.current_page-1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

async def show_view(interaction: discord.Interaction, view: MyView, init_embed: discord.Embed):
    await view.update()
    await interaction.response.send_message(embed=init_embed, view=view)
    message = await interaction.original_response()
    view.message = message
           