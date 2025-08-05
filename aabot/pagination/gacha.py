from io import StringIO

from discord import Color
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.crud.character import get_character
from aabot.pagination.embeds import BaseEmbed
from aabot.utils import api
from aabot.utils.emoji import to_emoji
from aabot.utils.utils import character_title
from common import schemas
from common.database import SessionAA
from common.enums import Element, Language, Server
from common.timezones import check_active, convert_from_jst

async def generate_banner_text(gacha_list: list[schemas.GachaPickup], session: AsyncSession, language: Language) -> str:
    banner_text = StringIO()
    for gacha in gacha_list:
        char_name = await api.fetch_name(gacha.char_id, language)
        element = Element((await get_character(session, gacha.char_id)).element)
        name = character_title(char_name.title, char_name.name)
        ongoing = (await to_emoji(session, "check")) if check_active(gacha.start, gacha.end, Server.Japan) else (await to_emoji(session, "x"))
        rerun_count = gacha.run_count

        # Format the text for each banner using StringIO
        banner_text.write(f"{await to_emoji(session, element)} **{name}**\n")
        banner_text.write(f"**Date:** <t:{convert_from_jst(gacha.start)}> ~ <t:{convert_from_jst(gacha.end)}>\n")
        banner_text.write(f"**Ongoing:** {ongoing} | **Run {rerun_count}**\n\n")

    return banner_text.getvalue()

async def generate_chosen_banner_text(chosen_list: list[schemas.GachaChosenGroup], session: AsyncSession, language: Language) -> str:
    banner_text = StringIO()
    for chosen in chosen_list:
        for gacha in chosen.banners:
            element = Element((await get_character(session, gacha.char_id)).element)
            char_name = await api.fetch_name(gacha.char_id, language)
            name = character_title(char_name.title, char_name.name)
            banner_text.write(f"- {await to_emoji(session, element)} **{name}** | **Run {gacha.run_count}**\n")

        ongoing = (await to_emoji(session, "check")) if check_active(gacha.start, gacha.end, Server.Japan) else (await to_emoji(session, "x"))

        banner_text.write(f"**Date:** <t:{convert_from_jst(chosen.start)}> ~ <t:{convert_from_jst(chosen.end)}>\n")
        banner_text.write(f"**Ongoing:** {ongoing}\n\n")

    return banner_text.getvalue()


async def gacha_banner_embed(gacha_data: schemas.APIResponse[schemas.GachaPickupBanners], language: Language):
    banners = gacha_data.data
    description = StringIO()

    embed = BaseEmbed(gacha_data.version, title="Gacha Banners", color=Color.blue())

    async with SessionAA() as session:
        # Fleeting field (select_list_type == 1)
        if banners.fleeting:
            description.write(f"### {await to_emoji(session, 'fleeting_s')} **Prayer of The Fleeting**\n")
            description.write(await generate_banner_text(banners.fleeting, session, language))

        # Chosen field (select_list_type == 4)
        if banners.chosen:
            description.write(f"### {await to_emoji(session, 'fleeting')} **Chosen Prayer of The Fleeting**\n")
            description.write(await generate_chosen_banner_text(banners.chosen, session, language))

        # Eminence field (select_list_type == 5)
        if banners.eminence:
            description.write(f"### {await to_emoji(session, 'eminence')} **Chosen Prayer of Eminence**\n")
            description.write(await generate_chosen_banner_text(banners.eminence, session, language))

        # IoC field (select_list_type == 2)
        if banners.ioc:
            description.write(f"### {await to_emoji(session, 'ioc')} **Invocation of Chance**\n")
            description.write(await generate_banner_text(banners.ioc, session, language))

        # IoSG field (select_list_type == 3)
        if banners.iosg:
            description.write(f"### {await to_emoji(session, 'iosg')} **Invocation of Stars' Guidance**\n")
            description.write(await generate_banner_text(banners.iosg, session, language))

        embed.description = description.getvalue()

    return embed