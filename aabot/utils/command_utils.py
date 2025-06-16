from enum import StrEnum
from functools import wraps
from typing import Callable

from discord import Interaction

from aabot.db.user import get_user
from common.database import AsyncSession as SessionAABot
# from common.enums import Language

# limit language options to officially supported languages
class LanguageOptions(StrEnum):  
    jajp = 'jajp'
    kokr = 'kokr'
    enus = 'enus'
    zhtw = 'zhtw'
    # dede = 'dede'
    # esmx = 'esmx'
    # frfr = 'frfr'
    # idid = 'idid'
    # ptbr = 'ptbr'
    # ruru = 'ruru'
    # thth = 'thth'
    # vivn = 'vivn'
    zhcn = 'zhcn'


def apply_user_preferences():
    """
    Decorator to apply user preferences for language, server, and world automatically.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            async with SessionAABot() as session:
                user_id = interaction.user.id
                user_pref = await get_user(session, user_id)

                if "language" in kwargs and kwargs["language"] is None:
                    kwargs["language"] = user_pref.language if user_pref and user_pref.language else LanguageOptions.enus

                if "server" in kwargs and kwargs["server"] is None:
                    if user_pref and user_pref.server:
                        kwargs["server"] = user_pref.server
                    else:
                        await interaction.response.send_message("Server must be specified. Alternatively use `/setpreference` to set a default server.", ephemeral=True)
                        return

                if "world" in kwargs and kwargs["world"] is None:
                    if user_pref and user_pref.world is not None:
                        kwargs["world"] = user_pref.world
                    else:
                        await interaction.response.send_message("World must be specified. Alternatively use `/setpreference` to set a default world.", ephemeral=True)
                        return

                return await func(self, interaction, *args, **kwargs)

        return wrapper
    return decorator

# decorator for char id check
# def check_id():
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(self, interaction: Interaction, *args, **kwargs):
#             character = kwargs.get('character', None) or args[0]
#             if not self.bot.masterdata.check_id(character):
#                 await interaction.response.send_message(
#                     f"A character id of `{character}` does not exist.",
#                     ephemeral=True
#                 )
#                 return
#             return await func(self, interaction, *args, **kwargs)
#         return wrapper
#     return decorator

# def in_range(num, start, end):
#     if num == '':
#         return True
#     num = int(num)
#     if start <= num <= end:
#         return True
#     if (start//10) <= num <= (end//10):
#         return True
#     if (start//100) <= num <= (end//100):
#         return True
#     return False

# async def group_autocomplete(
#         interaction: discord.Interaction, 
#         current: str) -> List[app_commands.Choice[str]]:
#     group_list = fetch_group_list(interaction.namespace.server)  # [(id, start, end), ...]

#     return [
#         app_commands.Choice(name=f'{choice[1]}-{choice[2]}', value=f'{choice[1]}-{choice[2]}')
#         for choice in group_list if in_range(current, choice[1], choice[2])
#     ]