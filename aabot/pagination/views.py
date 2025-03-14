from typing import Any, List
import discord

class MyView(discord.ui.View):
    def __init__(self, user: discord.User, **kwargs):  # kwargs to ignore if called from ButtonView
        super().__init__(timeout=180)
        self.user=user
        self.embed = None

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

class ButtonViewOLD(MyView):
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

class ButtonView(MyView):
    def __init__(self, user: discord.User, embed_dict: dict[str, list[discord.Embed]], key='default'):
        super().__init__(user, embed_dict=embed_dict, key=key)  # If MixedView calls DropdownView
        self.current_page = 1
        self.embed_dict = embed_dict
        self.embeds = self.embed_dict.get(key)
        self.max_page = len(self.embeds)
        self.embed = self.embeds[0] if self.embeds else None
        
        # Initialize buttons
        self.left2_btn = discord.ui.Button(label="<<", disabled=True)
        self.left_btn = discord.ui.Button(label="<", disabled=True)
        self.mid_btn = discord.ui.Button(label=f'1/{self.max_page}', disabled=True)
        self.right_btn = discord.ui.Button(label=">", disabled=True)
        self.right2_btn = discord.ui.Button(label=">>", disabled=True)

        self.left2_btn.callback = self.left2_btn_callback
        self.left_btn.callback = self.left_btn_callback
        self.right_btn.callback = self.right_btn_callback
        self.right2_btn.callback = self.right2_btn_callback
        
        self.add_item(self.left2_btn)
        self.add_item(self.left_btn)
        self.add_item(self.mid_btn)
        self.add_item(self.right_btn)
        self.add_item(self.right2_btn)

    async def update(self):
        # Update button states based on the current page
        self.left2_btn.disabled = self.current_page == 1
        self.left_btn.disabled = self.current_page == 1
        self.right_btn.disabled = self.current_page == self.max_page
        self.right2_btn.disabled = self.current_page == self.max_page
        self.mid_btn.label = f"{self.current_page}/{self.max_page}"

    async def left2_btn_callback(self, interaction: discord.Interaction):
        self.current_page = max(1, self.current_page - 10)
        self.embed = self.embeds[self.current_page - 1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def left_btn_callback(self, interaction: discord.Interaction):
        self.current_page = max(1, self.current_page - 1)
        self.embed = self.embeds[self.current_page - 1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def right_btn_callback(self, interaction: discord.Interaction):
        self.current_page = min(self.max_page, self.current_page + 1)
        self.embed = self.embeds[self.current_page - 1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def right2_btn_callback(self, interaction: discord.Interaction):
        self.current_page = min(self.max_page, self.current_page + 10)
        self.embed = self.embeds[self.current_page - 1]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

class DropdownView(MyView):
    def __init__(self, user: discord.User, embed_dict: dict[str, List[discord.Embed]], key='default'):
        super().__init__(user, embed_dict=embed_dict, key=key)  # If MixedView calls ButtonView
        self.key = key
        self.embed_dict = embed_dict
        self.embeds = self.embed_dict.get(key)
        self.embed = self.embeds[0]
        
        options = [discord.SelectOption(label=k, value=k) for k in embed_dict.keys()]
        self.dropdown = discord.ui.Select(
            placeholder="Choose an option...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.dropdown.callback = self.dropdown_callback
        self.add_item(self.dropdown)        
    
    async def update(self):
        for option in self.dropdown.options:
            option.default = (option.value == self.key)
    
    async def dropdown_callback(self, interaction: discord.Interaction):
        self.key = self.dropdown.values[0]
        self.embeds = self.embed_dict.get(self.key)
        self.embed = self.embeds[0]
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

class MixedView(DropdownView, ButtonView):
    def __init__(self, user: discord.User, embed_dict: dict[str, list[discord.Embed]], key='default'):
        super().__init__(user, embed_dict, key)

    async def update(self):
        self.left2_btn.disabled = self.current_page == 1
        self.left_btn.disabled = self.current_page == 1
        self.right_btn.disabled = self.current_page == self.max_page
        self.right2_btn.disabled = self.current_page == self.max_page
        self.mid_btn.label = f"{self.current_page}/{self.max_page}"
        
        for option in self.dropdown.options:
            option.default = (option.value == self.key)

    async def dropdown_callback(self, interaction: discord.Interaction):
        self.key = self.dropdown.values[0]
        self.embeds = self.embed_dict.get(self.key)
        self.embed = self.embeds[0]
        self.max_page = len(self.embeds)
        self.current_page = 1
        await self.update()
        await interaction.response.edit_message(embed=self.embed, view=self)

async def show_view(interaction: discord.Interaction, view: MyView, defered=False):
    await view.update()
    if defered:
        await interaction.followup.send(embed=view.embed, view=view)
    else:
        await interaction.response.send_message(embed=view.embed, view=view)
    message = await interaction.original_response()
    view.message = message
           