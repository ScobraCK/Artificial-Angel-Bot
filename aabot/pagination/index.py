from asyncio import gather
from aabot.pagination.embeds import BaseEmbed
from aabot.pagination.views import ButtonView, MixedView
from aabot.utils.emoji import character_string
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.utils import character_title, param_string
from common import enums, schemas

from discord import Color, Interaction

from io import StringIO
from itertools import batched

def id_list_view(interaction: Interaction, name_data: schemas.APIResponse[dict[int, schemas.Name]]):
    names = name_data.data.values()

    embeds = []
    for batch in batched(names, 50):
        description = StringIO()
        for name in batch:
            description.write(f"{name.char_id}: {character_title(name.title, name.name)}\n")
        embeds.append(
            BaseEmbed(
                name_data.version,
                title='Character Id',
                color=Color.green(),
                description=description.getvalue()
            )
        )

    return ButtonView(interaction.user, {'default': embeds})

async def arcana_basic_text(arcana: schemas.Arcana, cs: schemas.CommonStrings, language: enums.LanguageOptions):
    text = StringIO()

    text.write(f'**{arcana.name}**')
    if arcana.required_level > 0:
        text.write(f' ({cs.common.get('arcana level limit', 'Unlocked at Party Lv 300.')})')
    text.write('\n')
    text.write(f'{cs.common.get('characters', 'Characters')}: ')

    names = []
    for char in arcana.characters:
        char_str = await character_string(char, language)
        names.append(char_str)
    text.write(', '.join(names))

    bonus = []
    text.write('\n```\n')
    lr_level = next(filter(lambda x: x.rarity == enums.CharacterRarity.LR, arcana.levels))
    if lr_level.level_bonus:
        bonus.append(f'{cs.common.get('arcana bonus level', 'Max Party Lv')}: {lr_level.level_bonus}')
    for param in lr_level.parameters:
        bonus.append(param_string(param, cs))
    text.write('\n'.join(bonus))
    text.write('```\n')

    return text.getvalue()


async def arcana_detail_text(arcana: schemas.Arcana, cs: schemas.CommonStrings, language: enums.LanguageOptions):
    text = StringIO()
    text.write(f'**Required party level:** {arcana.required_level}\n')
    text.write(f'**{cs.common.get('characters', 'Characters')}:**\n')
    names = []
    for char in arcana.characters:
        char_str = await character_string(char, language)
        names.append(f'- {char_str}')
    text.write('\n'.join(names))
    text.write('\n\n')

    async def level_text(level: schemas.ArcanaLevel):
        text_ = StringIO()
        ic = ItemCounter(language)
        text_.write(f'**{cs.common.get('arcana', 'Arcana')} Lv {level.level}**\n')
        text_.write(f'**Rarity:** {level.rarity.name.replace('Plus', '+')}\n')
        ic.add_items(level.reward)
        items = await ic.get_total_strings()
        text_.write(f'**Reward:** {', '.join(items)}\n')

        bonus = []
        text_.write('```\n')
        if level.awaken_bonus:
            bonus.append(f'{cs.common.get('arcana awaken', 'Arcana Group Max Awaken.')}  {level.awaken_bonus}')

        if level.rarity >= enums.CharacterRarity.LR and level.parameters:
            bonus.append(f'{cs.common.get('arcana target', 'Enhanced Targets')}: {cs.common.get('arcana target all', 'All Characters')}')
        else:
            bonus.append(f'{cs.common.get('arcana target', 'Enhanced Targets')}: {cs.common.get('arcana target group', 'Arcana Group')}')

        if level.level_bonus:
            bonus.append(f'{cs.common.get('arcana bonus level', 'Max Party Lv')}: {level.level_bonus}')

        for param in level.parameters:
            bonus.append(param_string(param, cs))
        text_.write('\n'.join(bonus))
        text_.write('```')
        return text_.getvalue()

    text.write('\n'.join(await gather(*[level_text(level) for level in arcana.levels])))

    return text.getvalue()


async def arcana_view(
    interaction: Interaction,
    arcana_data: schemas.APIResponse[list[schemas.Arcana]],
    cs: schemas.CommonStrings,
    language: enums.LanguageOptions
):
    arcanas = arcana_data.data

    if len(arcanas) > 10:
        await interaction.response.defer(thinking=True)

    embed_dict = {
        'Basic': [],
        'Detailed': []
    }
    for arcana_batch in batched(arcanas, 5):
        basic_text = StringIO()
        for arcana in arcana_batch:
            basic_text.write(await arcana_basic_text(arcana, cs, language))
            embed_dict['Detailed'].append(
                BaseEmbed(
                    arcana_data.version,
                    title=arcana.name,
                    description=await arcana_detail_text(arcana, cs, language),
                    color=Color.purple()
                )
            )

        embed_dict['Basic'].append(
            BaseEmbed(
                arcana_data.version,
                title=cs.common.get('arcana', 'Arcana'),
                description=basic_text.getvalue(),
                color=Color.purple()
            ).set_footer(text='Arcana values shown for LR')
        )

    return MixedView(interaction.user, embed_dict, 'Basic')