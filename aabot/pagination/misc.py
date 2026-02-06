from io import StringIO
from itertools import dropwhile

from discord import ui

from aabot.crud.alias import get_alias
from aabot.pagination.view import BaseContainer
from aabot.utils import api
from aabot.utils.emoji import to_emoji
from aabot.utils.error import BotError
from aabot.utils.utils import character_title
from common.database import SessionAA
from common.enums import Server
from common.timezones import DailyEvents, time_to_local

async def alias_ui(character: int) -> BaseContainer:
    name = await api.fetch_name(character)
    container = BaseContainer(f'### Aliases for {character_title(name.title, name.name)}')
    async with SessionAA() as session:
        aliases = await get_alias(session, character)
        if not aliases:
            raise BotError(f'No alias found for character `{character}`.')

    default = []
    custom = []
    for alias in aliases:
        if alias.is_custom:
            custom.append(alias.alias)
        else:
            default.append(alias.alias)
    
    container.add_item(ui.TextDisplay(f'**Default Names**\n```\n{'\n'.join(default)}```'))
    container.add_item(ui.TextDisplay(f'**Aliases**\n```{'\n'.join(custom) if custom else "No alias"}```'))
    return container

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

def daily_ui() -> BaseContainer:
    option_map = {}
    for server in Server:
        container = BaseContainer(f'### Daily Information [{server.name}]')
        container.add_item(ui.TextDisplay(get_dailyinfo(server)))
        option_map[server.name] = container
    return option_map

#levellink
def get_sublevel(level: float)->tuple[int, int]:
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

async def levellink_ui(startlevel: float, endlevel: float|None) -> BaseContainer:
    container = BaseContainer(f'### Level Link Costs')
    startbase, startsub = get_sublevel(startlevel)
    if endlevel:
        endbase, endsub = get_sublevel(endlevel)
    else:
        endlevel = endbase = int((startbase+10) / 10) * 10  # next multiple of 10
        endsub = 0

    if startlevel < 240:
        return BaseContainer("Currently only levellink(240+) is supported.")

    if startlevel > endlevel:
        raise BotError(f"`startlevel` should be lower than `endlevel`. Got `{startlevel}` and `{endlevel}`.")

    link_resp = await api.fetch_api(
        api.MASTER_PATH.format(mb='LevelLinkMB'),
        response_model=list[dict]
    )               
    link_data_list = link_resp.data
    
    max_level = link_data_list[-1]['PartyLevel']
    if endbase == max_level + 1:
        endsub = 0

    if startlevel > max_level or endbase > max_level+1:
        return BaseContainer(f"Max level is {max_level}.9")
    else:
        level_data = dropwhile(lambda x: level_predicate(x, startbase, startsub), link_data_list)
        total_gold = 0
        total_gorb = 0
        total_rorb = 0
        for level in level_data:
            if level['PartyLevel'] == endbase and level['PartySubLevel'] == endsub:  # end
                break
            costs = level['RequiredLevelUpItems']
            total_gold += costs[0]["ItemCount"]  # gold
            total_gorb += costs[1]["ItemCount"]  # green orbs
            if len(costs) == 3:
                total_rorb += costs[2]["ItemCount"]  # red orbs
    
    async with SessionAA() as session:
        container.add_item(
            ui.TextDisplay(f'**__{startbase}.{startsub} -> {endbase}.{endsub}__**')
        ).add_item(ui.TextDisplay(
            f'{await to_emoji(session, 'gold')}×{total_gold:,d}\n'
            f'{await to_emoji(session, 'green_orb')}×{total_gorb:,d}\n'
            f'{await to_emoji(session, 'red_orb')}×{total_rorb:,d}'
        ))

    return container