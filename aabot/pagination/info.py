from asyncio import gather
from io import StringIO
from itertools import batched, chain

from discord import ButtonStyle, Interaction, ui

from aabot.pagination.skills import get_skill_name, get_skill_text
from aabot.pagination.view import BaseContainer, BaseView, to_content
from aabot.utils import api
from aabot.utils.assets import SKILL_THUMBNAIL
from aabot.utils.command_utils import ArcanaOption
from aabot.utils.emoji import character_string, char_ele_emoji, to_emoji
from aabot.utils.itemcounter import ItemCounter
from aabot.utils.utils import character_title, param_string
from common import enums, schemas
from common.database import SessionAA


async def id_list_ui(language: enums.LanguageOptions, page_limit: int = 20) -> list[BaseContainer]:
    containers = []
    name_resp = await api.fetch_api(
        api.STRING_CHARACTER_PATH,
        query_params={'language': language},
        response_model=dict[int, schemas.Name]
    )

    for batch in batched(name_resp.data.values(), page_limit):
        text = StringIO()
        for name in batch:
            text.write(f'**{name.char_id}:** {await char_ele_emoji(name.char_id)} {character_title(name.title, name.name)}\n')
        container = (
            BaseContainer()
            .add_item(ui.TextDisplay('### Character Ids'))
            .add_item(ui.TextDisplay(text.getvalue()))
            .add_version(name_resp.version)
        ) 
        containers.append(container)
    return containers

class SpeedModal(ui.Modal):
    def __init__(self, view: BaseView, default_flat: int, default_mult: int, page_limit: int):
        super().__init__(title="Speed modifiers")
        self.view = view
        self.page_limit = page_limit
        self.flat_label = ui.Label(
            text='Flat speed additions',
            component=ui.TextInput(default=str(default_flat), required=False),
        )
        self.mult_label = ui.Label(
            text='Speed buff percentage',
            component=ui.TextInput(default=str(default_mult), required=False),
            description='Ex) 10 is +10% speed buff. 0 is no buff.'
        )
        self.add_item(self.flat_label).add_item(self.mult_label)
        
    async def on_submit(self, interaction: Interaction):
        flat = self.flat_label.component.value
        mult = self.mult_label.component.value
        if not flat.isdigit() or not mult.isdigit():
            await interaction.response.send_message(
                "Input must be an integer.",
                ephemeral=True
            )
            return
        self.view.save_navigation()
        self.view.replace_content_map(  # cannot use partial for pages
            to_content(await speed_ui(language=self.view.language, flat=int(flat), mult=int(mult), page_limit=self.page_limit))
        )
        self.view.load_navigation()
        await self.view.update_view(interaction)

async def speed_ui(language: enums.LanguageOptions, flat: int = 0, mult: int = 0, page_limit: int = 20) -> BaseContainer:
    containers = []
    speed_resp = await api.fetch_api(
        api.CHARACTER_SEARCH_PATH,
        response_model=list[schemas.CharacterDBModel],
        query_params={'option': 'speed'}
    )
    name_resp = await api.fetch_api(
        api.STRING_CHARACTER_PATH,
        query_params={'language': language},
        response_model=dict[int, schemas.Name]
    )
    name_data = name_resp.data

    button = ui.Button(label='Change Modifiers', style=ButtonStyle.primary)
    async def callback(interaction: Interaction):
        modal = SpeedModal(button.view, flat, mult, page_limit)
        await interaction.response.send_modal(modal)
    button.callback = callback
    
    modifier_text = f'Flat bonus: {flat}\nBuff multiplier: {mult}%'

    i = 1
    async with SessionAA() as session:
        for batch in batched(reversed(speed_resp.data), page_limit):
            text = StringIO()
            for char in batch:
                name = name_data[char.id]
                speed = int((char.speed + flat) * (1 + mult / 100))
                text.write(f'**{i}.** {speed} | {await to_emoji(session, enums.Element(char.element))} {character_title(name.title, name.name)}\n')
                i += 1
            container = (
                BaseContainer()
                .add_item(ui.TextDisplay('### Character Speeds'))
                .add_item(ui.TextDisplay(text.getvalue()))
                .add_item(ui.Separator())
                .add_item(ui.Section(
                    ui.TextDisplay('### Modifiers'),
                    ui.TextDisplay(modifier_text),
                    accessory=button
                ))
                .add_version(name_resp.version)
            ) 
            containers.append(container)
   
    return containers

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

async def arcana_search_ui(character: int|None, option: ArcanaOption|None, cs: schemas.CommonStrings, language: enums.LanguageOptions):
    arcana_resp = await api.fetch_api(
        api.ARCANA_SEARCH_PATH,
        response_model=list[schemas.Arcana],
        query_params={
            'character': character,
            'param_category': option.category,
            'param_type': option.type,
            'param_change_type': option.change_type,
            'level_bonus': option.level_bonus,
            'language': language
        }
    )
    arcana_data = arcana_resp.data
    content_map = {'Basic': [], 'Detailed': []}

    for arcana_batch in batched(arcana_data, 5):
        basic = (
            BaseContainer()
            .add_item(ui.TextDisplay(f'### {cs.common.get('arcana', 'Arcana')}\nValues shown for LR'))
            .add_item(ui.Separator())
        )

        for arcana in arcana_batch:
            basic.add_item(ui.TextDisplay(await arcana_basic_text(arcana, cs, language))).add_item(ui.Separator(visible=False))
            content_map['Detailed'].append(
                BaseContainer()
                .add_item(ui.TextDisplay(f'### {arcana.name}'))
                .add_item(ui.TextDisplay(await arcana_detail_text(arcana, cs, language)))
                .add_version(arcana_resp.version)
            )
        content_map['Basic'].append(basic.add_version(arcana_resp.version))

    return content_map

async def skill_detail_ui(character: int, language: enums.LanguageOptions):
    skill_resp = await api.fetch_api(
        api.CHARACTER_SKILL_PATH.format(char_id=character),
        query_params={'language': language},
        response_model=schemas.Skills
    )
    skill_data = skill_resp.data

    content_map = {}
    async with SessionAA() as session:
        for skill in chain(skill_data.actives, skill_data.passives):
            pages = []
            title = None  # used as flag. If None use skill.name + thumbnail
            thumbnail = SKILL_THUMBNAIL.format(skill_id=skill.id)

            # Main Container (First page)
            main_container = BaseContainer()
            description = await get_skill_text(skill, skill_data.uw_descriptions, session)
            if skill.name == '*' or not skill.name:
                # Alt skills such as Rosalie(SR), Paladea
                if (uw_rarity := skill.skill_infos[0].uw_rarity) == 0 and skill.skill_infos[0].level in {1, 21, 41, 81, 121, 161, 181}:  # active skill levels
                    title = f'Alternative Skill Trigger (ID: {skill.id})'
                elif uw_rarity > 0 and isinstance(skill, schemas.PassiveSkill):
                    title = f'Unique Weapon Passive (ID: {skill.id})'
                else:
                    title = f'Unknown Skill (ID: {skill.id})'
                main_container.add_item(ui.TextDisplay(f'### {title}'))
                main_container.add_item(ui.TextDisplay(description))
                
            else:
                main_container.add_item(
                    ui.Section(
                        ui.TextDisplay(f'### {skill.name} (ID: {skill.id})'),
                        ui.TextDisplay(description),
                        accessory=ui.Thumbnail(thumbnail)
                    )
                )

            main_container.add_version(skill_resp.version)
            pages.append(main_container)

            # Detail pages
            for info in skill.skill_infos:
                detail_container = BaseContainer()
                uw_rarity_str = enums.ItemRarity(info.uw_rarity).name
                # Common
                if uw_rarity_str:
                    if skill_data.uw_descriptions:
                        info_description = f'{getattr(skill_data.uw_descriptions, uw_rarity_str)}\n\n'
                    else:  # Not in data
                        info_description = 'Description unavailable.\n\n'
                else:
                    info_description = f'{info.description}\n\n'

                if title:
                    detail_container.add_item(ui.TextDisplay(f'### {title}'))
                    detail_container.add_item(ui.TextDisplay(info_description))
                else:
                    detail_container.add_item(
                        ui.Section(
                            ui.TextDisplay(f'### {skill.name}'),
                            ui.TextDisplay(info_description),
                            accessory=ui.Thumbnail(thumbnail)
                        )
                    )

                detail_container.add_item(ui.TextDisplay(
                    '**Details**\n' 
                    f'```json\n'
                    f'Order Number: {info.order_number}\n'
                    f'Character Level: {info.level}\n'
                    f'Equipment Rarity: {uw_rarity_str}```'
                ))
                # Active
                if isinstance(skill, schemas.ActiveSkill):
                    detail_container.add_item(ui.TextDisplay(
                        '**Cooldown Info**\n'
                        f'```json\n'
                        f'Init CD: {skill.init_cooltime}\n'
                        f'Max CD: {skill.max_cooltime}```'
                    )).add_item(ui.TextDisplay(
                        '**Subskills**\n'
                        f'```json\n{'\n'.join(map(str, info.subskill))}```'
                    ))
                # Passive
                else:
                    subskill_text = StringIO()
                    subskill_text.write('**Subskills**\n')
                    subskills: list[schemas.PassiveSubSkill] = info.subskill
                    for sub in subskills:
                        subskill_text.write(
                            '```json\n'
                            f'Passive Trigger: {enums.PassiveTrigger(sub.trigger).name}({sub.trigger})\n'
                            f'Initial CD: {sub.init_cooltime}\n'
                            f'Max CD: {sub.max_cooltime}\n'
                            f'Group Id: {sub.group_id}\n'
                            f'Subskill Id: {sub.subskill_id}```'
                        )
                    detail_container.add_item(ui.TextDisplay(subskill_text.getvalue()))
                detail_container.add_version(skill_resp.version)
                pages.append(detail_container)

            if title:
                content_map[title] = pages
            else:
                content_map[skill.name] = pages
    return content_map



            