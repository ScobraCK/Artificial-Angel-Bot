from discord import Color, Embed, Interaction, MediaGalleryItem, app_commands, ui
from discord.ext import commands


from aabot.main import AABot
from aabot.pagination import misc as misc_ui
from aabot.pagination.view import BaseView, BaseContainer
from aabot.utils import api
from aabot.utils.alias import IdTransformer
from aabot.utils.assets import RAW_ASSET_BASE
from aabot.utils.command_utils import apply_user_preferences
from common.enums import Server

class MiscCommands(commands.Cog, name='Misc Commands'):
    '''These are helpful miscellaneous commands'''

    def __init__(self, bot: AABot):
        self.bot = bot
    
    @app_commands.command()
    async def awakening(self, interaction: Interaction):
        '''Awakening cost chart'''
        container = BaseContainer()
        img = RAW_ASSET_BASE + 'Bot/awakening_costs.png'
        container.add_item(ui.MediaGallery(MediaGalleryItem(img)))
        view = BaseView(container, interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    async def soulaffinity(self, interaction: Interaction):
        '''Soul affinity chart'''
        container = BaseContainer()
        img = RAW_ASSET_BASE + 'Bot/soul_affinity.jpg'
        container.add_item(ui.MediaGallery(MediaGalleryItem(img)))
        view = BaseView(container, interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    async def enhancecost(self, interaction: Interaction):
        '''Equipment enhancement cost chart'''
        container = BaseContainer()
        img = RAW_ASSET_BASE + 'Bot/enhance.png'
        container.add_item(ui.MediaGallery(MediaGalleryItem(img)))
        view = BaseView(container, interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    async def seteffect(self, interaction: Interaction):
        '''Equipment set effect chart'''
        container = BaseContainer()
        img = RAW_ASSET_BASE + 'Bot/seteffects.png'
        container.add_item(ui.MediaGallery(MediaGalleryItem(img)))
        view = BaseView(container, interaction.user)
        await view.update_view(interaction)

    @app_commands.command()
    @apply_user_preferences()
    async def dailyinfo(
        self,
        interaction: Interaction, 
        server: Server|None = None
    ):
        '''list of notable daily events shown in local time'''
        view = BaseView(misc_ui.daily_ui(), interaction.user, default_option=server.name)
        await view.update_view(interaction)

    # TODO redo levellink
    @app_commands.command()
    @app_commands.describe(
        startlevel='specify sublevel if required. 240(=240.0), 240.1, 240.9',
        endlevel='rounds to the next power of 10 if empty (sublevel is 0)'
    )
    async def levellink(
        self,
        interaction: Interaction,
        startlevel: float,
        endlevel: float|None):
        '''
        Calculate level link costs.
        '''
        view = BaseView(await misc_ui.levellink_ui(startlevel, endlevel), interaction.user)
        await view.update_view(interaction)
        
    @app_commands.command()
    @app_commands.describe(
        character = 'The name or id of the character'
    )
    async def alias(
        self,
        interaction: Interaction,
        character: app_commands.Transform[int, IdTransformer]
    ):
        '''Show aliases for a character'''
        view = BaseView(await misc_ui.alias_ui(character), interaction.user)
        await view.update_view(interaction)


async def setup(bot: AABot):
	await bot.add_cog(MiscCommands(bot))