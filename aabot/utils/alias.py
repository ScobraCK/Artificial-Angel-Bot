from re import sub

from discord import Interaction, app_commands
from fuzzywuzzy import process, fuzz
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from aabot.crud.alias import get_all_alias, insert_alias
from aabot.utils import api
from aabot.utils.error import BotError

from common.database import SessionAA
from common.enums import LanguageOptions
from common.models import Alias
from common.schemas import Name


def normalize_alias(string: str):
    pattern = r"[^\w\s]"
    return sub(pattern, '', string).lower()

async def alias_lookup(session: AsyncSession, alias: str) -> int:
    alias_list = await get_all_alias(session)
    alias2id = {alias_.alias: alias_.char_id for alias_ in alias_list}
    char, _ = process.extractOne(normalize_alias(alias), alias2id.keys(), scorer=fuzz.ratio)

    return alias2id[char]

async def add_alias(session: AsyncSession, char_id: int, alias: str, is_custom=False, ignore_duplicate=False) -> Alias:
    try:
        result = await insert_alias(session, char_id, normalize_alias(alias), is_custom=is_custom)
        return result
    except IntegrityError as e:
        await session.rollback()
        if ignore_duplicate:
            return None
        raise BotError(f'Alias {alias} already exists.')

async def autoalias(session: AsyncSession, char_id: int, serial: int=None) -> list[str]:
    '''Automatically adds default alias. Add serial for quick adding alt character numbers.'''
    aliases = []
    for language in LanguageOptions:
        char_name = await api.fetch_name(char_id, language)
        name = char_name.name
        if serial is not None:
            name = f'{name}{serial}'
        alias = await add_alias(session, char_id, name, ignore_duplicate=True)
        if alias:
            aliases.append(alias.alias)
        if title := char_name.title:
            alias_title = await add_alias(session, char_id, title, ignore_duplicate=True)
            if alias_title:
                aliases.append(alias_title.alias)
    
    return aliases

async def autoalias_all(session: AsyncSession) -> list[str]:
    '''Reruns autoalias for all characters. Used for new languages or missed chars.'''
    aliases = []
    name_count = {}
    resp = await api.fetch_api(
        api.STRING_CHARACTER_PATH,
        response_model=dict[int, Name]
    )
    ids = resp.data.keys()
    
    for char_id in ids:
        name = resp.data[char_id].name
        if name in name_count:
            name_count[name] += 1
            serial = name_count[name]
        else:
            name_count[name] = 1
            serial = None
        new_aliases = await autoalias(session, char_id, serial)
        aliases.extend(new_aliases)
    return aliases

# transformer for id
class IdTransformer(app_commands.Transformer):
    async def transform(self, interaction: Interaction, value: str) -> int:
        try:
            id = int(value)
        except ValueError:
            async with SessionAA() as session:
                id = await alias_lookup(session, value)
        return id
