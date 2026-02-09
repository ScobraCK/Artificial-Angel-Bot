from discord import Color, ui

from aabot.utils import api
from aabot.pagination.view import BaseContainer
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.emoji import to_emoji
from aabot.utils.utils import make_table, param_string, remove_html
from common import enums, schemas
from common.database import SessionAA

async def item_ui(item_id: int, item_type: int, language: enums.Language, cs: schemas.CommonStrings) -> BaseContainer:
    container = BaseContainer()
    TITLE_TEXT = 1
    item_response = await api.fetch_item(item_id, item_type, language)
    item_data = item_response.data
    thumbnail = None  # TODO add thumbnail support
    
    title = f'### {item_data.name}'
    basic_text = (
        f'**Id:** {item_data.id}\n'
        f'**Item id:** {item_data.item_id}\n'
        f'**Item type:** {enums.ItemType(item_type).name}({item_type})\n'
        f'**Max:** {item_data.max_count if item_data.max_count else "No limit"}\n'
    )

    # Thumbnail Section to be added later
    if thumbnail:
        container.add_item(
            ui.Section(
                ui.TextDisplay(title, id=TITLE_TEXT),
                ui.TextDisplay(basic_text),
                accessory=ui.Thumbnail(thumbnail)
            )
        )
    else:
        container.add_item(
            ui.TextDisplay(title, id=TITLE_TEXT)
        ).add_item(
            ui.TextDisplay(basic_text)
        )
    
    container.add_item(
        ui.TextDisplay(f'**Description**\n{remove_html(item_data.description)}')
    )

    if isinstance(item_data, schemas.Rune):
        container.find_item(TITLE_TEXT).content = f'{title} Lv.{item_data.level}'
        container.add_item(
            ui.TextDisplay(
                '**Details**\n'
                f'Type: {item_data.category.name}\n'
                f'Level: {item_data.level}\n'
                f'Parameter: {param_string(item_data.parameter, cs)}'
            )
        )

    return container

#TODO make a better UI
async def rune_ui(rune_type: enums.RuneType, language: enums.Language, cs: schemas.CommonStrings) -> BaseContainer:
    ic = ItemCounter(language)
    container = BaseContainer()
    rune_resp = await api.fetch_api(
        path=api.ITEM_RUNE_CATEGORY_PATH,
        path_params={'category': rune_type},
        query_params={'language': language},
        response_model=list[schemas.Rune]
    )
    
    rune_data = rune_resp.data
    container.add_item(
        ui.TextDisplay(f'### {rune_data[0].name}')
    ).add_item(
        ui.TextDisplay(f'{remove_html(rune_data[0].description)}')
    ).add_item(ui.Separator())

    async with SessionAA() as session:
        for rune in rune_data:
            ic.add_items(rune.combine_cost)
            container.add_item(
                ui.TextDisplay(
                    f'**Lv.{rune.level}** (ID: {rune.id})\n**Value:** {rune.parameter.value}\n'
                    f'**Cost:** {await to_emoji(session, 'rune_ticket')}x{2**rune.level} | **Merge:** {' '.join(await ic.get_total_strings())}\n'
                )
            )
            ic.clear()

    container.add_version(rune_resp.version)
    return container
