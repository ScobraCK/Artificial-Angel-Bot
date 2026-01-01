from collections import namedtuple
from collections.abc import Callable
from functools import wraps

from discord import Interaction, app_commands

from aabot.crud.user import get_user
from common import enums
from common.database import SessionAA

def apply_user_preferences():
    """
    Decorator to apply user preferences for language, server, and world automatically.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            async with SessionAA() as session:
                user_id = interaction.user.id
                user_pref = await get_user(session, user_id)

                if "language" in kwargs and kwargs["language"] is None:
                    kwargs["language"] = user_pref.language if user_pref and user_pref.language else enums.LanguageOptions.enus

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


ArcanaOption = namedtuple('ArcanaOption', ['category', 'type', 'change_type', 'level_bonus'], defaults=(None, None, None, None))
ArcanaOptions = {
    'STR Flat': ArcanaOption('Base', 1, 1),
    'STR Chara. Lv': ArcanaOption('Base', 1, 3),
    'DEX Flat': ArcanaOption('Base', 2, 1),
    'DEX Chara. Lv': ArcanaOption('Base', 2, 3),
    'MAG Flat': ArcanaOption('Base', 3, 1),
    'MAG Chara. Lv': ArcanaOption('Base', 3, 3),
    'STA Flat': ArcanaOption('Base', 4, 1),
    'STA Chara. Lv': ArcanaOption('Base', 4, 3),
    'HP Percent': ArcanaOption('Battle', 1, 2),
    'ATK Flat': ArcanaOption('Battle', 2, 1),
    'ATK Percent': ArcanaOption('Battle', 2, 2),
    'P.DEF Flat': ArcanaOption('Battle', 3, 1),
    'P.DEF Percent': ArcanaOption('Battle', 3, 2),
    'M.DEF Flat': ArcanaOption('Battle', 4, 1),
    'M.DEF Percent': ArcanaOption('Battle', 4, 2),
    'ACC Flat': ArcanaOption('Battle', 5, 1),
    'ACC Percent': ArcanaOption('Battle', 5, 2),
    'ACC Chara. Lv': ArcanaOption('Battle', 5, 3),
    'EVD Flat': ArcanaOption('Battle', 6, 1),
    'EVD Chara. Lv': ArcanaOption('Battle', 6, 3),
    'CRIT Chara. Lv': ArcanaOption('Battle', 7, 3),
    'CRIT RES Flat': ArcanaOption('Battle', 8, 1),
    'CRIT RES Chara. Lv': ArcanaOption('Battle', 8, 3),
    'CRIT DMG Boost Flat': ArcanaOption('Battle', 9, 1),
    'P.CRIT DMG Cut Flat': ArcanaOption('Battle', 10, 1),
    'M.CRIT DMG Cut Flat': ArcanaOption('Battle', 11, 1),
    'DEF Break Flat': ArcanaOption('Battle', 12, 1),
    'DEF Percent': ArcanaOption('Battle', 13, 2),
    'DEF Chara. Lv': ArcanaOption('Battle', 13, 3),
    'PM.DEF Break Flat': ArcanaOption('Battle', 14, 1),
    'Debuff ACC Percent': ArcanaOption('Battle', 15, 2),
    'Debuff ACC Chara. Lv': ArcanaOption('Battle', 15, 3),
    'Debuff RES Flat': ArcanaOption('Battle', 16, 1),
    'Debuff RES Chara. Lv': ArcanaOption('Battle', 16, 3),
    'Counter Flat': ArcanaOption('Battle', 17, 1),
    'HP Drain Flat': ArcanaOption('Battle', 18, 1),
    'Level Bonus': ArcanaOption(None, None, None, True)
}

async def arcana_autocomplete(interaction: Interaction, current: str):
    choices = [
        app_commands.Choice(name=opt, value=opt)
        for opt in ArcanaOptions
        if current.replace('.', '').lower() in opt.replace('.', '').lower()
    ]
    return choices[:25]

async def itemtype_autocomplete(interaction: Interaction, current: int):
    if not current:
        choices = [
            app_commands.Choice(name=f'{opt.name}({opt.value})', value=opt.value)
            for opt in list(enums.ItemType)[:25]
        ]
    else:
        current_str = str(current)
        choices = [
            app_commands.Choice(name=f'{opt.name}({opt.value})', value=opt.value)
            for opt in enums.ItemType
            if str(opt.value).startswith(current_str)
        ]
    return choices


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
#         current: str) -> list[app_commands.Choice[str]]:
#     group_list = fetch_group_list(interaction.namespace.server)  # [(id, start, end), ...]

#     return [
#         app_commands.Choice(name=f'{choice[1]}-{choice[2]}', value=f'{choice[1]}-{choice[2]}')
#         for choice in group_list if in_range(current, choice[1], choice[2])
#     ]