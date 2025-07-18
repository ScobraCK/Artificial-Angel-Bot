from discord import app_commands, Interaction
from discord.ext import commands

from aabot.db.alias import delete_alias
from aabot.main import AABot
from aabot.utils import api
from aabot.utils.alias import add_alias, auto_alias
from common.database import AsyncSession as SessionAABot

class AdminCommands(commands.Cog, name='Admin Commands'):
    '''Admin Commands'''

    def __init__(self, bot):
        self.bot: AABot = bot

    async def interaction_check(self, interaction: Interaction):
        return await self.bot.is_owner(interaction.user)

    @app_commands.command()
    async def updateguilds(
        self,
        interaction: Interaction
    ):
        '''
        Updates api guild rankings
        '''
        await interaction.response.defer()
        await api.fetch(
            api.UPDATE_API_GUILD_PATH,
            base_url=api.API_BASE_PATH,
            params={'key': self.bot.api_key},
            timeout=60
        )
        await interaction.followup.send('Successfully updated guilds.')

    @app_commands.command()
    @commands.is_owner()
    async def updateplayers(
        self,
        interaction: Interaction
    ):
        '''
        Updates api player rankings
        '''
        await interaction.response.defer()
        await api.fetch(
            api.UPDATE_API_PLAYERS_PATH,
            base_url=api.API_BASE_PATH,
            params={'key': self.bot.api_key},
            timeout=60
        )
        await interaction.followup.send('Successfully updated players.')

    @app_commands.command()
    async def updatemaster(
        self,
        interaction: Interaction
    ):
        '''
        Updates api master. 
        '''
        await interaction.response.defer()
        await api.fetch(api.UPDATE_PATH, base_url=api.API_BASE_PATH, params={'key': self.bot.api_key}, timeout=60)
        # data = response.json()
        # updated = data.get('data')
        # chars = data.get('new_chars')

        # aliases = []
        # async with SessionAABot() as session:
        #     for char in chars:
        #         aliases.extend(await auto_alias(session, char))

        await interaction.followup.send(
            'Successfully updated masterdata.'
        )

    @app_commands.command()
    async def updatestrings(
        self,
        interaction: Interaction
    ):
        '''
        Updates api strings. 
        '''
        await interaction.response.defer()
        await api.fetch(f'{api.API_BASE_PATH}{api.UPDATE_STR_PATH}', params={'key': self.bot.api_key}, timeout=60)
        await interaction.followup.send('Successfully updated strings.')

    @app_commands.command()
    async def updatechars(
        self,
        interaction: Interaction
    ):
        '''
        Updates api chars. 
        '''
        await interaction.response.defer()
        response = await api.fetch(f'{api.API_BASE_PATH}{api.UPDATE_CHAR_PATH}', params={'key': self.bot.api_key}, timeout=60)
        data = response.json()
        chars = data.get('new')
        aliases = []
        async with SessionAABot() as session:
            for char in chars:
                await auto_alias(session, char)

        await interaction.followup.send(
            'Successfully updated characters.\n'
            f'Characters added: {str(chars) if chars else 'None'}\n\n'
        )
    
    @app_commands.command()
    async def addalias(
        self,
        interaction: Interaction,
        character: int,
        alias: str
    ):
        async with SessionAABot() as session:
            result = await add_alias(session, character, alias, is_custom=True)
            await interaction.response.send_message(f'Added alias `{result.alias}` for character {result.char_id}')

    @app_commands.command()
    async def autoalias(
        self,
        interaction: Interaction,
        character: int,
        serial: int|None
    ):
        async with SessionAABot() as session:
            results = await auto_alias(session, character, serial=serial)
            aliases = ', '. join((f'`{alias.alias}`' for alias in results))
            await interaction.response.send_message(f'Added aliases {aliases} for character {character}')

    @app_commands.command()
    async def deletealias(
        self,
        interaction: Interaction,
        alias: str
    ):
        async with SessionAABot() as session:
            result = await delete_alias(session, alias)
            if result:
                await interaction.response.send_message(f'Removed alias `{alias}`.')
            else:
                await interaction.response.send_message(f'Alias `{alias}` did not exist.')
        
async def setup(bot: AABot):
    await bot.add_cog(AdminCommands(bot))
 