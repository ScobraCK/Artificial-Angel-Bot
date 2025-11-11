import inspect
from dataclasses import dataclass
from typing import Callable, Awaitable

import discord
from discord import ui, SelectOption

from aabot.utils.error import BotError, ContentError
from common.enums import Language
from common.schemas import CommonStrings

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

MAIN_CONTAINER_ID = 1000
PAGE_ROW_ID = 1100
BUTTON1_ID = 1101
BUTTON2_ID = 1102
BUTTON3_ID = 1103
BUTTON4_ID = 1104
BUTTON5_ID = 1105
SELECT_ROW_ID = 1200
SELECT_ID = 1201

# Content Map
@dataclass
class BaseContent:
    # Holds a page's container directly or a factory producing it (sync/async)
    content: ui.Container | Callable[..., ui.Container | Awaitable[ui.Container]]

    async def get_content(self, language: Language | None = None, cs: CommonStrings | None = None) -> ui.Container:
        try:
            if callable(self.content):
                sig = inspect.signature(self.content)
                kwargs = {}
                if 'language' in sig.parameters:
                    kwargs['language'] = language
                if 'cs' in sig.parameters:
                    kwargs['cs'] = cs
                result = self.content(**kwargs)
                if inspect.isawaitable(result):
                    result = await result
                return result
        except BotError:
            raise ContentError()
        return self.content

@dataclass
class ContentPage:
    pages: list[BaseContent]

    @property
    def page_count(self) -> int:
        return len(self.pages)

@dataclass
class ContentSelect:
    options: dict[str, ContentPage | Callable[..., ContentPage | Awaitable[ContentPage]]]

    @property
    def keys(self) -> list[str]:
        return list(self.options.keys())

    async def get_option(self, key: str, language: Language | None = None, cs: CommonStrings | None = None) -> ContentPage:
        pages = self.options[key]
        try:
            if callable(pages):
                sig = inspect.signature(pages)
                kwargs = {}
                if 'language' in sig.parameters:
                    kwargs['language'] = language
                if 'cs' in sig.parameters:
                    kwargs['cs'] = cs
                result = pages(**kwargs)
                if inspect.isawaitable(result):
                    result = await result
                return result
        except BotError:
            raise ContentError()
        return pages

@dataclass
class ContentMap:
    content: ContentSelect|ContentPage

    @property
    def keys(self) -> list[str]|None:
        if isinstance(self.content, ContentSelect):
            return self.content.keys
        return None
    
    @property
    def page_count(self) -> int|None:
        if isinstance(self.content, ContentPage):
            return self.content.page_count
        return None

def _to_content_page(
    raw_pages: ui.Container | Callable[..., ui.Container | Awaitable[ui.Container]] | list[ui.Container | Callable[..., ui.Container | Awaitable[ui.Container]]]
) -> ContentPage:
    """Convert a list of page definitions (each page is a container or a factory) into a ContentPage."""
    pages: list[BaseContent] = []
    if isinstance(raw_pages, ui.Container) or callable(raw_pages):
        return ContentPage(pages=[BaseContent(content=raw_pages)])  # Single container (lazy check)
    for page in raw_pages:
        pages.append(BaseContent(content=page))
    return ContentPage(pages=pages)

def to_content(raw: dict[str, list] | list | ui.Container | Callable[..., ui.Container | Awaitable[ui.Container]]) -> ContentMap:
    """Convert raw contents (or factories) into a ContentMap."""
    if isinstance(raw, dict):
        options: dict[str, ContentPage | Callable[..., ContentPage | Awaitable[ContentPage]]] = {}
        for key, value in raw.items():
            if callable(value):
                async def _factory(language: Language | None = None, cs: CommonStrings | None = None, v=value):
                    try:
                        sig = inspect.signature(v)
                        kwargs = {}
                        if 'language' in sig.parameters:
                            kwargs['language'] = language
                        if 'cs' in sig.parameters:
                            kwargs['cs'] = cs
                        res = v(**kwargs)
                        if inspect.isawaitable(res):
                            res = await res
                    except BotError as e:
                        raise ContentError() from e
                    if isinstance(res, ContentPage):
                        return res
                    return _to_content_page(res)
                options[key] = _factory
            else:
                options[key] = _to_content_page(value)
        return ContentMap(content=ContentSelect(options=options))

    if isinstance(raw, list) or isinstance(raw, ui.Container) or callable(raw):
        return ContentMap(content=_to_content_page(raw))

    raise TypeError('Unsupported raw content type for to_content()')


# View
class BaseView(ui.LayoutView):
    def __init__(
            self,
            content_map: ContentMap,
            user: discord.User,
            language: Language|None = None,
            cs: CommonStrings|None = None,
            original_response: discord.InteractionMessage|None = None,
            default_page: int = 0,  # 0 indexed
            default_option: str|None = None
        ):
        super().__init__(timeout=240)
        self.user = user
        self.language = language
        self.cs = cs
        self.original_response = original_response
        self.content_map = content_map
        self.page = default_page
        self.option = default_option or content_map.keys[0] if content_map.keys else None  # Given default or first option is default. None if no options.
        self._nav_cache: dict = {}
        self._option_cache: dict[str, ContentPage] = {}
        self.main_content = MainContent(id=MAIN_CONTAINER_ID)
        self.page_nav = PageNavigation(id=PAGE_ROW_ID)
        self.option_nav = OptionNavigation(id=SELECT_ROW_ID)

        self.add_item(self.main_content)
        self.add_item(self.page_nav)
        self.add_item(self.option_nav)
        
    async def update_view(self, interaction: discord.Interaction):
        try:
            await self.update_content()
        except ContentError:
            await interaction.response.send_message('Failed to fetch content', ephemeral=True)
            return
        self.timeout = 240  # Reset timeout on interaction
        if self.main_content.content_length == 0:
            raise BotError('No content to display')

        if interaction.response.is_done():  # defered
            if self.original_response is None:  # Only if defered outside of view
                self.original_response = await interaction.original_response()
                await self.original_response.edit(view=self)
            else:
                await interaction.edit_original_response(view=self)
        elif interaction.message is None:  # First response (send through view)
            callback = await interaction.response.send_message(view=self)
            self.original_response = callback.resource
        else:  # update
            await interaction.response.edit_message(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        check = (interaction.user.id == self.user.id)
        if not check:
            await interaction.response.send_message(
                'Only the original command user can change this',
                ephemeral=True
            )
        return check

    async def on_timeout(self):
        for item in self.walk_children():
            if item.type in (discord.ComponentType.button, discord.ComponentType.select):
                item.disabled = True  # TODO check if URL buttons are affected when needed
        if self.original_response:  # Unlikely to be None
            await self.original_response.edit(view=self)

    async def get_content(self, page: int = 0, option: str|None = None) -> ui.Container:
        content_page = await self._get_content_page(option)
        base_content = content_page.pages[page]
        return await base_content.get_content(language=self.language, cs=self.cs)
        
    async def update_content(self):
        content_page = await self._get_content_page()

        # Clamp page in case content changed
        if self.page >= content_page.page_count:
            self.page = content_page.page_count - 1
        if self.page < 0:
            self.page = 0

        content = await content_page.pages[self.page].get_content(language=self.language, cs=self.cs)
        self.main_content.update_content(content)
        self.update_navigation()

    def replace_content_map(self, content_map: ContentMap, page: int = 0, option: str|None = None):
        self.content_map = content_map
        self.invalidate_option_cache()
        self.page = page
        self.option = option

    def save_navigation(self):
        self._nav_cache['page'] = self.page
        self._nav_cache['option'] = self.option

    def load_navigation(self):
        self.page = self._nav_cache.get('page', 0)
        self.option = self._nav_cache.get('option', None)

    def _get_page_count(self) -> int:
        if isinstance(self.content_map.content, ContentSelect):
            cached = self._option_cache.get(self.option)
            if cached is not None:
                return cached.page_count
            # Fallback to 1 to keep navigation usable until update_content runs
            return 1
        return self.content_map.content.page_count

    async def _get_content_page(self, option: str|None = None) -> ContentPage:
        content = self.content_map.content
        if isinstance(content, ContentSelect):
            key = option if option is not None else self.option
            assert key is not None, "Option key must not be None when using ContentSelect"
            cached = self._option_cache.get(key)
            if cached is not None:
                return cached
            content_page = await content.get_option(key, language=self.language, cs=self.cs)
            self._option_cache[key] = content_page
            return content_page
        return content

    def invalidate_option_cache(self, key: str|None = None):
        # Allow callers to invalidate cached ContentPages if upstream data changes
        if key is None:
            self._option_cache.clear()
        else:
            self._option_cache.pop(key, None)
    
    def update_navigation(self):
        # Page Navigation
        page_count = self._get_page_count()
        if page_count > 1:
            left2: ui.Button = self.page_nav.find_item(BUTTON1_ID)
            left: ui.Button = self.page_nav.find_item(BUTTON2_ID)
            mid: ui.Button = self.page_nav.find_item(BUTTON3_ID)
            right: ui.Button = self.page_nav.find_item(BUTTON4_ID)
            right2: ui.Button = self.page_nav.find_item(BUTTON5_ID)

            left2.disabled = (self.page == 0)
            left.disabled = (self.page == 0)
            right.disabled = (self.page >= page_count - 1)
            right2.disabled = (self.page >= page_count - 1)
            mid.label = f'{self.page + 1}/{page_count}'

            if self.page_nav not in self.children:
                if self.option_nav in self.children:
                    self.remove_item(self.option_nav)  # Maintain navigation bar order
                self.add_item(self.page_nav)
        else:
            if self.page_nav in self.children:
                self.remove_item(self.page_nav)
        # Select Option
        if self.content_map.keys:
            select: ui.Select = self.option_nav.find_item(SELECT_ID)
            if not select.options:
                select.options = [
                    SelectOption(label=key, value=key, default=(key == self.option))
                    for key in self.content_map.keys
                ]
            else:
                for option in select.options:
                    option.default = (option.value == self.option)
            if self.option_nav not in self.children:
                self.add_item(self.option_nav)
        else:
            if self.option_nav in self.children:
                self.remove_item(self.option_nav)   # There should not be a case when option removes itself (potential parent-child disconnect issue if it happens)


class MainContent(ui.Container):
    def __init__(self, *children, accent_colour = None, accent_color = None, spoiler = False, id = None):
        super().__init__(*children, accent_colour=accent_colour, accent_color=accent_color, spoiler=spoiler, id=id)

    def update_content(self, content: ui.Container):
        self.clear_items()
        for item in content.children:
            self.add_item(item)

class PageNavigation(ui.ActionRow):
    @ui.button(label='<<', id=BUTTON1_ID)
    async def left2_btn(self, interaction: discord.Interaction, button: ui.Button):
        self.view.page = 0
        await self.view.update_view(interaction)

    @ui.button(label='<', id=BUTTON2_ID)
    async def left_btn(self, interaction: discord.Interaction, button: ui.Button):
        self.view.page = max(0, self.view.page - 1)
        await self.view.update_view(interaction)

    @ui.button(label='1/1', disabled=True, id=BUTTON3_ID)
    async def mid_btn(self, interaction: discord.Interaction, button: ui.Button):
        pass  # TODO add page navigator

    @ui.button(label='>', id=BUTTON4_ID)
    async def right_btn(self, interaction: discord.Interaction, button: ui.Button):
        self.view.page = min(self.view._get_page_count() - 1, self.view.page + 1)
        await self.view.update_view(interaction)

    @ui.button(label='>>', id=BUTTON5_ID)
    async def right2_btn(self, interaction: discord.Interaction, button: ui.Button):
        self.view.page = self.view._get_page_count() - 1
        await self.view.update_view(interaction)

class OptionNavigation(ui.ActionRow):
    @ui.select(id=SELECT_ID)
    async def select_menu(self, interaction: discord.Interaction, select: ui.Select):
        self.view.option = select.values[0]
        self.view.page = 0  # Reset page to first when changing option
        await self.view.update_view(interaction)

class EmptyContent(ui.Container):
    def __init__(self, message: str = 'Selected content is currently unavailable.'):
        super().__init__()
        self.add_item(ui.TextDisplay(message))

def create_content_button(content, label: str, page: int = 0, option: str|None = None, save_state: bool = False, load_state: bool = False) -> ui.Button:
    button = ui.Button(label=label)
    async def callback(interaction: discord.Interaction):
        view: BaseView = button.view
        if save_state:
            view.save_navigation()
        view.replace_content_map(to_content(content), page=page, option=option)
        if load_state:
            view.load_navigation()
        await view.update_view(interaction)
    button.callback = callback
    return button