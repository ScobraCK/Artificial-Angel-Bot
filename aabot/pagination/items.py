from collections import namedtuple

from discord import Color, Interaction

from aabot.utils import api
from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import DynamicMixedView
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.utils import make_table, param_string, remove_html
from common import enums, schemas

rarity_color = {
    1: Color.default(),
    2: Color.default(),
    4: Color.default(),
    8: Color.default(),
    16: Color.default(),
    32: Color.from_str('#aeb5bf'),
    64: Color.from_str('#d9af5b'),
    128: Color.from_str('#8d54ab'),
    256: Color.from_str('#c0474e'),
    512: Color.from_str('#272c26'),
}

def item_embed(item_data: schemas.APIResponse[schemas.Item], cs: schemas.CommonStrings):
    item = item_data.data
    title = item.name
    description = (
        f'**Id:** {item.id}\n'
        f'**Item id:** {item.item_id}\n'
        f'**Item type:** {enums.ItemType(item.item_type).name}({item.item_type})\n'
        f'Max: {item.max_count if item.max_count else 'No limit'}\n\n'
        f'**Description**\n{remove_html(item.description)}\n\n'
    )
    
    if isinstance(item, schemas.Rune):
        title = f'{title} Lv.{item.level}'
        description += (
            '**Details**\n'
            f'Type: {cs.rune_type[item.category]}\n'
            f'Level: {item.level}\n'
            f'Parameter: {param_string(item.parameter, cs)}'
        )
    
    return BaseEmbed(
        item_data.version,
        title=title,
        description=description,
        color=rarity_color.get(item.rarity)
    )

async def rune_callable(rune_type: enums.RuneType, cs: schemas.CommonStrings, language: enums.Language)->dict[str, list[BaseEmbed]]:
    ic = ItemCounter()
    rune_data = await api.fetch_api(
        path=api.ITEM_RUNE_CATEGORY_PATH,
        path_params={'category': rune_type},
        query_params={'language': language},
        response_model=list[schemas.Rune]
    )
    
    detail_embeds = []
    level_data = []
    for rune in rune_data.data:
        # Basic info
        level_data.append([rune.level, f'{rune.parameter.value:,}', f'{2**rune.level:,}'])
        # Detailed info
        ic.add_items(rune.combine_cost)
        detail_embeds.append(
            BaseEmbed(
                rune_data.version,
                title=f'{rune.name} Lv.{rune.level}',
                description=(
                    f'**Id:** {rune.id}\n'
                    f'**Type:** {cs.rune_type[rune.category]}\n'
                    f'**Level:** {rune.level}\n'
                    f'**Value:** {rune.parameter.value}\n'
                    f'**Description:**\n```\n{remove_html(rune.description)}```'
                    f'**Combine Costs:**\n```\n{'\n'.join(await ic.get_total_strings())}```\n'
                ),
                color=Color.blurple()
            )
        )
        ic.clear()

    basic_embed = BaseEmbed(
        rune_data.version,
        title=f'{rune.name}',
        description=f'```prolog\n{make_table(level_data, header=['Level', 'Value', 'Cost(Tickets)'], style='ascii_simple')}```',
        color=Color.blurple()
    )
    return {'Basic Info': [basic_embed], f'Details': detail_embeds}

        
async def rune_view(interaction: Interaction, rune: enums.RuneType, cs: schemas.CommonStrings, language: enums.Language):
    view = DynamicMixedView(
        interaction.user,
        callable_=rune_callable,
        callable_options={x.name: {'rune_type': x, 'cs': cs, 'language': language} for x in enums.RuneType},
        embed_dict=await rune_callable(rune, cs, language),
        callable_key=rune.name,
        key='Basic Info'
    )
    return view