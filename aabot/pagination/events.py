from discord import Embed, Color
from io import StringIO
from typing import List


from aabot.api import api, response
from aabot.pagination.embeds import BaseEmbed
from aabot.utils import emoji, enums
from aabot.utils.utils import character_title
from aabot.utils.timezones import get_cur_timestamp_UTC

async def generate_banner_text(gacha_list: List[response.GachaPickup], language: enums.Language):
    current = get_cur_timestamp_UTC()
    banner_text = StringIO()
    for gacha in gacha_list:
        name_data = await api.fetch_name(gacha.char_id, language)
        name = character_title(name_data.data.title, name_data.data.name)
        ongoing = ":white_check_mark:" if gacha.start <= current <= gacha.end else ":x:"  # Ongoing status
        rerun_count = gacha.run_count

        # Format the text for each banner using StringIO
        banner_text.write(f"**{name}**\n")
        banner_text.write(f"**Date:** <t:{gacha.start}> ~ <t:{gacha.end}>\n")
        banner_text.write(f"**Ongoing:** {ongoing} | **Run {rerun_count}**\n\n")

    return banner_text.getvalue()


async def gacha_banner_embed(gacha_data: response.APIResponse[List[response.GachaPickup]], language: enums.Language):
    fleeting = []
    ioc = []
    iosg = []
    
    for gacha in gacha_data.data:
        if gacha.gacha_type == 1:
            fleeting.append(gacha)
        elif gacha.gacha_type == 2:
            ioc.append(gacha)
        elif gacha.gacha_type == 3:
            iosg.append(gacha)
        
    embed = BaseEmbed(gacha_data.version, title="Gacha Banners", color=Color.blue())

    # Fleeting field (select_list_type == 1)
    embed.add_field(name=f"{emoji.item_emoji[9]}**Prayer of Fleeting**{emoji.item_emoji[9]}", value=await generate_banner_text(fleeting, language), inline=False)

    # IoC field (select_list_type == 2)
    embed.add_field(name=f"{emoji.item_emoji[54]}**Invocation of Chance**{emoji.item_emoji[54]}", value=await generate_banner_text(ioc, language), inline=False)

    # IoSG field (select_list_type == 3)
    embed.add_field(name=f"{emoji.item_emoji[121]}**Invocation of Stars' Guidance**{emoji.item_emoji[121]}", value=await generate_banner_text(iosg, language), inline=False)

    return embed