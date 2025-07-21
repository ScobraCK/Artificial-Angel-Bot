import discord
from collections.abc import Callable
from typing import Awaitable

from aabot.utils.error import BotError

class BaseView(discord.ui.View):
    def __init__(
            self,
            user: discord.User,
            embed_dict: dict[str, list[discord.Embed]],
            key='default'):
        super().__init__(timeout=240)
        self.user=user
        self.message: discord.InteractionMessage|None = None
        self.embed_dict = embed_dict
        self.embeds = embed_dict.get(key, [])
        self.embed: discord.Embed|None = self.embeds[0] if self.embeds else None
        self._key = key  # default key

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

    async def update_view(self, interaction: discord.Interaction):
        '''Updates the actual message'''
        await self.update()
        self.timeout = 240  # Reset timeout on update

        if self.embed is None:
            raise BotError('Embed data is empty.')
        
        if interaction.response.is_done():
            if self.message is None:  # Only if defered outside of view
                self.message = await interaction.original_response()
                await self.message.edit(embed=self.embed, view=self)  # Test: used to be followup
            else:
                await interaction.edit_original_response(embed=self.embed, view=self)
        elif interaction.message is None:
            callback = await interaction.response.send_message(embed=self.embed, view=self)
            self.message = callback.resource
        else:
            await interaction.response.edit_message(embed=self.embed, view=self)

    async def update(self) -> None:
        '''Override to update the view state'''
        pass

    async def reset_items(self) -> None:
        '''Override to reset the UI state for parent classes'''
        pass

class PageSelect(discord.ui.Modal):
    def __init__(self, max_page: int):
        super().__init__(title="Select Page")
        self.page = discord.ui.TextInput(label="Page", placeholder="Enter a page number", required=True, min_length=1, max_length=3)
        self.max_page = max_page
        self.add_item(self.page)
        
    async def on_submit(self, interaction: discord.Interaction):
        if not self.page.value.isdigit():
            await interaction.response.send_message(
                "Input must be a valid page number.",
                ephemeral=True
            )
            return
        if int(self.page.value) < 1 or int(self.page.value) > self.max_page:
            await interaction.response.send_message(
                f"Page number must be between 1 and {self.max_page}.",
                ephemeral=True
            )
            return
        # Defer the response to acknowledge the modal submission without sending a message
        await interaction.response.defer()
        
class ButtonView(BaseView):
    def __init__(self, user: discord.User, embed_dict: dict[str, list[discord.Embed]], key='default'):
        super().__init__(user, embed_dict=embed_dict, key=key)
        self.current_page = 1
        self.max_page = len(self.embeds)
        
        # Initialize buttons
        self.left2_btn = discord.ui.Button(label="<<", disabled=True)
        self.left_btn = discord.ui.Button(label="<", disabled=True)
        self.mid_btn = discord.ui.Button(label=f'1/{self.max_page}')
        self.right_btn = discord.ui.Button(label=">", disabled=True)
        self.right2_btn = discord.ui.Button(label=">>", disabled=True)

        self.left2_btn.callback = self.left2_btn_callback
        self.left_btn.callback = self.left_btn_callback
        self.mid_btn.callback = self.mid_btn_callback
        self.right_btn.callback = self.right_btn_callback
        self.right2_btn.callback = self.right2_btn_callback
        
        self.add_item(self.left2_btn)
        self.add_item(self.left_btn)
        self.add_item(self.mid_btn)
        self.add_item(self.right_btn)
        self.add_item(self.right2_btn)

    async def update(self):
        await super().update()
        # No data
        if self.max_page == 0:
            return
        # Update button states based on the current page
        self.left2_btn.disabled = self.current_page == 1
        self.left_btn.disabled = self.current_page == 1
        self.right_btn.disabled = self.current_page == self.max_page
        self.right2_btn.disabled = self.current_page == self.max_page
        self.mid_btn.disabled = self.max_page <= 1
        self.mid_btn.label = f"{self.current_page}/{self.max_page}"

    async def reset_items(self):  # self.embeds have changed
        self.current_page = 1
        self.max_page = len(self.embeds)
        await super().reset_items()

    async def left2_btn_callback(self, interaction: discord.Interaction):
        self.current_page = 1
        self.embed = self.embeds[self.current_page - 1]
        await self.update_view(interaction)

    async def left_btn_callback(self, interaction: discord.Interaction):
        self.current_page = max(1, self.current_page - 1)
        self.embed = self.embeds[self.current_page - 1]
        await self.update_view(interaction)

    async def mid_btn_callback(self, interaction: discord.Interaction):
        modal = PageSelect(self.max_page)
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        page = modal.page.value  # check for view (separate from modal)
        if not page.isdigit() or int(page) < 1 or int(page) > self.max_page:
            return
        
        self.current_page = int(modal.page.value)
        self.embed = self.embeds[self.current_page - 1]
        await self.update_view(interaction)
    
    async def right_btn_callback(self, interaction: discord.Interaction):
        self.current_page = min(self.max_page, self.current_page + 1)
        self.embed = self.embeds[self.current_page - 1]
        await self.update_view(interaction)

    async def right2_btn_callback(self, interaction: discord.Interaction):
        self.current_page = self.max_page
        self.embed = self.embeds[self.current_page - 1]
        await self.update_view(interaction)

class DropdownView(BaseView):
    def __init__(self, user: discord.User, embed_dict: dict[str, list[discord.Embed]], key='default'):
        super().__init__(user, embed_dict=embed_dict, key=key)  # If MixedView calls ButtonView
        self.key = key
        
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
        await super().update()
        for option in self.dropdown.options:
            option.default = (option.value == self.key)

    async def reset_items(self):  # self.embed_dict has changed
        self.key = self._key
        self.dropdown.options = [discord.SelectOption(label=k, value=k) for k in self.embed_dict.keys()]
        await super().reset_items()
    
    async def dropdown_callback(self, interaction: discord.Interaction):
        self.key = self.dropdown.values[0]
        self.embeds = self.embed_dict.get(self.key, [])
        self.embed = self.embeds[0] if self.embeds else None
        await super().reset_items()  # calls button view reset if applicable
        await self.update_view(interaction)

class DynamicView(BaseView):
    '''
    Adds a dropdown menu that will change the entire embed dict (affects dropdowns and buttons).
    - callable: Callable that returns the embed_dict: dict[str, list[discord.Embed]].
    - callable_options: dict[str, dict] with keys as option labels and values as dicts for the calalble kwargs.
    - embed_dict: Initial embed_dict to use.
    - callable_key: Default callable key to use when the view is initialized.
    - key: Default key to use for the embed_dict.
    '''
    def __init__(
            self,
            user: discord.User,
            callable_: Callable[..., Awaitable[dict[str, list[discord.Embed]]]],
            callable_options: dict[str, dict],
            embed_dict: dict[str, list[discord.Embed]],
            callable_key='default',
            key='default'
        ):
        super().__init__(user, embed_dict=embed_dict, key=key)
        self.callable = callable_
        self.callable_options = callable_options
        self.callable_key = callable_key
        
        options = [discord.SelectOption(label=k, value=k) for k in callable_options.keys()]
        self.dynamic_dropdown = discord.ui.Select(
            placeholder="Choose an option...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.dynamic_dropdown.callback = self.dynamic_dropdown_callback
        self.add_item(self.dynamic_dropdown)

    async def update(self):
        await super().update()
        for option in self.dynamic_dropdown.options:
            option.default = (option.value == self.callable_key)

    async def dynamic_dropdown_callback(self, interaction: discord.Interaction):
        self.callable_key = self.dynamic_dropdown.values[0]
        self.embed_dict = await self.callable(**(self.callable_options.get(self.callable_key, {})))
        self.embeds = self.embed_dict.get(self._key, [])
        self.embed = self.embeds[0] if self.embeds else None
        await super().reset_items()
        await self.update_view(interaction)

class MixedView(DropdownView, ButtonView):
    def __init__(self, user: discord.User, embed_dict: dict[str, list[discord.Embed]], key='default'):
        super().__init__(user, embed_dict, key)

class DynamicButtonView(DynamicView, ButtonView):
    def __init__(self, user: discord.User, callable_: Callable[..., Awaitable[dict[str, list[discord.Embed]]]], callable_options: dict[str, dict], embed_dict: dict[str, list[discord.Embed]], callable_key='default', key='default'):
        super().__init__(user, callable_, callable_options, embed_dict, callable_key, key)

class DynamicDropdownView(DynamicView, DropdownView):
    def __init__(self, user: discord.User, callable_: Callable[..., Awaitable[dict[str, list[discord.Embed]]]], callable_options: dict[str, dict], embed_dict: dict[str, list[discord.Embed]], callable_key='default', key='default'):
        super().__init__(user, callable_, callable_options, embed_dict, callable_key, key)

class DynamicMixedView(DynamicView, MixedView):
    def __init__(self, user: discord.User, callable_: Callable[..., Awaitable[dict[str, list[discord.Embed]]]], callable_options: dict[str, dict], embed_dict: dict[str, list[discord.Embed]], callable_key='default', key='default'):
        super().__init__(user, callable_, callable_options, embed_dict, callable_key, key)

# Now redundant, but kept in case it is needed
async def show_view(interaction: discord.Interaction, view: BaseView):
    await view.update_view(interaction)
