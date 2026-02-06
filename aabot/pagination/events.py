from io import StringIO

from discord import ui
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.crud.character import get_character
from aabot.pagination.view import BaseContainer
from aabot.utils import api
from aabot.utils.assets import CHARACTER_THUMBNAIL
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

        ongoing = (await to_emoji(session, "check")) if check_active(chosen.start, chosen.end, Server.Japan) else (await to_emoji(session, "x"))

        banner_text.write(f"**Date:** <t:{convert_from_jst(chosen.start)}> ~ <t:{convert_from_jst(chosen.end)}>\n")
        if isinstance(chosen, schemas.GachaEminenceGroup):
            banner_text.write(f"**Ongoing:** {ongoing} | **Limit:** {chosen.limit_days} days\n\n")
        else:
            banner_text.write(f"**Ongoing:** {ongoing}\n\n")

    return banner_text.getvalue()

async def gacha_banner_ui(language: Language, character: int = None):
    TEMP_TEXT = 1
    container = BaseContainer()
    if character:
        query_params = {
            'char_id': character,
            'is_active': False
        }
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'### Gacha History'),
                ui.TextDisplay('', id=TEMP_TEXT),
                accessory=ui.Thumbnail(CHARACTER_THUMBNAIL.format(char_id=character, qlipha=False))
            )
        )
    else:
        query_params = {
            'include_future': True
        }
        container.add_item(ui.TextDisplay('### Gacha Banners'))

    gacha_resp = await api.fetch_api(
        api.GACHA_PATH,
        response_model=schemas.GachaPickupBanners,
        query_params=query_params
    )
    gacha_data = gacha_resp.data

    async with SessionAA() as session:
        # Fleeting field (select_list_type == 1)
        if gacha_data.fleeting:
            container.add_item(
                ui.Separator()
            ).add_item(
                ui.TextDisplay(f'{await to_emoji(session, "fleeting_s")} __**Prayer of The Fleeting**__')
            # ).add_item(
            #     ui.Separator()
            ).add_item(ui.TextDisplay(await generate_banner_text(gacha_data.fleeting, session, language)))

        # Chosen field (select_list_type == 4)
        if gacha_data.chosen:
            container.add_item(
                ui.Separator()
            ).add_item(
                ui.TextDisplay(f'{await to_emoji(session, "fleeting")} __**Chosen Prayer of The Fleeting**__')
            ).add_item(ui.TextDisplay(await generate_chosen_banner_text(gacha_data.chosen, session, language)))

        # Eminence field (select_list_type == 5)
        if gacha_data.eminence:
            container.add_item(
                ui.Separator()
            ).add_item(
                ui.TextDisplay(f'{await to_emoji(session, "eminence")} __**Chosen Prayer of Eminence**__')
            # ).add_item(
            #     ui.Separator()
            ).add_item(ui.TextDisplay(await generate_chosen_banner_text(gacha_data.eminence, session, language)))

        # IoC field (select_list_type == 2)
        if gacha_data.ioc:
            container.add_item(
                ui.Separator()
            ).add_item(
                ui.TextDisplay(f'{await to_emoji(session, "ioc")} __**Invocation of Chance**__')
            # ).add_item(
            #     ui.Separator()
            ).add_item(ui.TextDisplay(await generate_banner_text(gacha_data.ioc, session, language)))

        # IoSG field (select_list_type == 3)
        if gacha_data.iosg:
            container.add_item(
                ui.Separator()
            ).add_item(
                ui.TextDisplay(f'{await to_emoji(session, "iosg")} __**Invocation of Stars\' Guidance**__')
            # ).add_item(
            #     ui.Separator()
            ).add_item(ui.TextDisplay(await generate_banner_text(gacha_data.iosg, session, language)))

    # add additional information for character gacha history
    if character:
        if gacha_data.iosg:
            max_run = max(banner.run_count for banner in gacha_data.iosg)
        else:
            max_run = max(banner.run_count for banner in gacha_data.ioc)
        container.find_item(TEMP_TEXT).content = f'**Total runs:** {max_run}'

    return container
