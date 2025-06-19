from io import StringIO
from typing import List

from discord import Color

from aabot.pagination.embeds import BaseEmbed
from aabot.utils import api, emoji
from aabot.utils.utils import character_title
from common import schemas
from common.enums import Language, Server
from common.timezones import check_active, convert_from_jst

async def generate_banner_text(gacha_list: List[schemas.GachaPickup], language: Language, name_dict: dict = {}) -> str:
    banner_text = StringIO()
    for gacha in gacha_list:
        if gacha.char_id in name_dict:
            name = name_dict[gacha.char_id]
        else:
            name_data = await api.fetch_name(gacha.char_id, language)
            name = character_title(name_data.data.title, name_data.data.name)
            name_dict[gacha.char_id] = name
        ongoing = ":white_check_mark:" if check_active(gacha.start, gacha.end, Server.Japan) else ":x:"  # Ongoing status
        rerun_count = gacha.run_count

        # Format the text for each banner using StringIO
        banner_text.write(f"**{name}**\n")
        banner_text.write(f"**Date:** <t:{convert_from_jst(gacha.start)}> ~ <t:{convert_from_jst(gacha.end)}>\n")
        banner_text.write(f"**Ongoing:** {ongoing} | **Run {rerun_count}**\n\n")

    return banner_text.getvalue()


async def gacha_banner_embed(gacha_data: schemas.APIResponse[List[schemas.GachaPickup]], language: Language):
    fleeting = []
    ioc = []
    iosg = []
    name_dict = {}
    
    for gacha in gacha_data.data:
        if gacha.gacha_type == 1:
            fleeting.append(gacha)
        elif gacha.gacha_type == 2:
            ioc.append(gacha)
        elif gacha.gacha_type == 3:
            iosg.append(gacha)
        
    embed = BaseEmbed(gacha_data.version, title="Gacha Banners", color=Color.blue())

    # Fleeting field (select_list_type == 1)
    embed.add_field(name=f"{emoji.item_emoji[9]}**Prayer of Fleeting**{emoji.item_emoji[9]}", value=await generate_banner_text(fleeting, language, name_dict), inline=False)

    # IoC field (select_list_type == 2)
    embed.add_field(name=f"{emoji.item_emoji[54]}**Invocation of Chance**{emoji.item_emoji[54]}", value=await generate_banner_text(ioc, language, name_dict), inline=False)

    # IoSG field (select_list_type == 3)
    embed.add_field(name=f"{emoji.item_emoji[121]}**Invocation of Stars' Guidance**{emoji.item_emoji[121]}", value=await generate_banner_text(iosg, language, name_dict), inline=False)

    return embed