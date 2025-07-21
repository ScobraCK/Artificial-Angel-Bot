from io import StringIO

from discord import Color

from aabot.pagination.embeds import BaseEmbed
from aabot.utils import api, emoji
from aabot.utils.utils import character_title
from common import schemas
from common.enums import Language, Server
from common.timezones import check_active, convert_from_jst

async def generate_banner_text(gacha_list: list[schemas.GachaPickup], language: Language) -> str:
    banner_text = StringIO()
    for gacha in gacha_list:
        char_name = await api.fetch_name(gacha.char_id, language)
        name = character_title(char_name.title, char_name.name)
        ongoing = ":white_check_mark:" if check_active(gacha.start, gacha.end, Server.Japan) else ":x:"  # Ongoing status
        rerun_count = gacha.run_count

        # Format the text for each banner using StringIO
        banner_text.write(f"**{name}**\n")
        banner_text.write(f"**Date:** <t:{convert_from_jst(gacha.start)}> ~ <t:{convert_from_jst(gacha.end)}>\n")
        banner_text.write(f"**Ongoing:** {ongoing} | **Run {rerun_count}**\n\n")

    return banner_text.getvalue()

async def generate_chosen_banner_text(chosen_list: list[schemas.GachaChosenGroup], language: Language) -> str:
    banner_text = StringIO()
    for chosen in chosen_list:
        for gacha in chosen.banners:
            char_name = await api.fetch_name(gacha.char_id, language)
            name = character_title(char_name.title, char_name.name)
            banner_text.write(f"- **{name}** | **Run {gacha.run_count}**\n")
            
        ongoing = ":white_check_mark:" if check_active(chosen.start, chosen.end, Server.Japan) else ":x:"  # Ongoing status
        
        banner_text.write(f"**Date:** <t:{convert_from_jst(chosen.start)}> ~ <t:{convert_from_jst(chosen.end)}>\n")
        banner_text.write(f"**Ongoing:** {ongoing}\n\n")

    return banner_text.getvalue()


async def gacha_banner_embed(gacha_data: schemas.APIResponse[schemas.GachaBanners], language: Language):
    banners = gacha_data.data

    embed = BaseEmbed(gacha_data.version, title="Gacha Banners", color=Color.blue())

    # Fleeting field (select_list_type == 1)
    embed.add_field(name=f"{emoji.item_emoji[9]}**Prayer of The Fleeting**{emoji.item_emoji[9]}", value=await generate_banner_text(banners.fleeting, language), inline=False)
    
    embed.add_field(name=f'{emoji.item_emoji[9]}**Chosen Prayer of The Fleeting**{emoji.item_emoji[9]}', value=await generate_chosen_banner_text(banners.chosen, language), inline=False)

    # IoC field (select_list_type == 2)
    embed.add_field(name=f"{emoji.item_emoji[54]}**Invocation of Chance**{emoji.item_emoji[54]}", value=await generate_banner_text(banners.ioc, language), inline=False)

    # IoSG field (select_list_type == 3)
    embed.add_field(name=f"{emoji.item_emoji[121]}**Invocation of Stars' Guidance**{emoji.item_emoji[121]}", value=await generate_banner_text(banners.iosg, language), inline=False)

    return embed