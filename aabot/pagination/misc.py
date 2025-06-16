from io import StringIO
from typing import List, Tuple

from discord import Color, Embed, Interaction

from aabot.pagination.views import DropdownView
from common.enums import Server
from common.models import Alias
from common.timezones import DailyEvents, time_to_local

def alias_embed(name: str, aliases: List[Alias]):
    description = StringIO()
    default = []
    custom = []
    for alias in aliases:
        if alias.is_custom:
            custom.append(alias.alias)
        else:
            default.append(alias.alias)
    
    description.write('**Default Names**\n')
    description.write(f'```\n{'\n'.join(default)}```\n')
    description.write('**Aliases**\n')
    description.write(f'```{'\n'.join(custom) if custom else 'No alias'}```')

    embed = Embed(
        title=f'Aliases for {name}',
        description=description.getvalue(),
        color=Color.green()
    )

    return embed

def get_dailyinfo(server: Server):
    text = StringIO()
    info = DailyEvents()
    local = time_to_local
    text.write(f'<t:{local(info.reset, server)}:t> Daily Server Reset\n')
    text.write(f'<t:{local(info.shop1, server)}:t> Free Shop Reset A\n')
    text.write(f'<t:{local(info.shop2, server)}:t> Free Shop Reset B\n')
    text.write(f'<t:{local(info.shop3, server)}:t> Free Shop Reset C\n')
    text.write(f'<t:{local(info.shop4, server)}:t> Free Shop Reset D\n\n')
    text.write(f'<t:{local(info.temple_open1, server)}:t>~<t:{local(info.temple_close1, server)}:t> Temple of Illusion Boost\n')
    text.write(f'<t:{local(info.temple_open2, server)}:t>~<t:{local(info.temple_close2, server)}:t> Temple of Illusion Boost\n\n')
    text.write(f'<t:{local(info.pvp_reset, server)}:t> PvP Reset\n')
    text.write(f'<t:{local(info.legend_league_start, server)}:t> Legend League Start (Tuesday~Sunday)\n\n')
    text.write(f'<t:{local(info.guild_strategy_start, server)}:t>~<t:{local(info.guild_strategy_end, server)}:t> Guild/Grand Battle: Strategy Phase\n')
    text.write(f'<t:{local(info.guild_war_start, server)}:t>~<t:{local(info.guild_war_end, server)}:t> Guild/Grand Battle: War Phase\n\n')

    return text.getvalue()

def daily_embed(server: Server):
    server_name = server.name

    embed=Embed(
        title = f'Daily Information [{server_name}]',
        description=get_dailyinfo(server),
        color=Color.blue()
        )
    return embed

def daily_view(interaction: Interaction, server: Server):
    return DropdownView(interaction.user, {s.name: [daily_embed(s)] for s in Server}, server.name) 

########## levellink #################
def get_sublevel(level: float)->Tuple[int, int]:
    level = str(level)
    try:
        base, sub = level.split('.')
        base = int(base)
        sub = int(sub[0])
    except ValueError:
        base = int(level)
        sub = 0

    return base, sub


def level_predicate(leveldata, base, sub):
    if leveldata['PartyLevel'] < base:
        return True
    if leveldata['PartySubLevel'] < sub:
        return True
    return False
