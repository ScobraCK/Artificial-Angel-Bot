from discord import Interaction, app_commands
from fuzzywuzzy import process, fuzz
from re import sub
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List

from aabot.api import api
from aabot.db.crud import get_all_alias, insert_alias
from aabot.db.database import SessionAABot
from aabot.db.models import Alias
from aabot.utils.enums import Language
from aabot.utils.error import BotError

from aabot.utils.logger import get_logger
logger = get_logger(__name__)

def normalize_alias(string: str):
    pattern = r"[^\w\s]"
    return sub(pattern, '', string).lower()

def alias_lookup(session: Session, alias: str) -> int:
    alias_list = get_all_alias(session)
    alias2id = {alias_.alias: alias_.char_id for alias_ in alias_list}
    char, _ = process.extractOne(normalize_alias(alias), alias2id.keys(), scorer=fuzz.ratio)

    return alias2id[char]

def add_alias(session: Session, char_id: int, alias: str, is_custom=False, ignore_duplicate=False) -> Alias:
    try:
        result = insert_alias(session, char_id, normalize_alias(alias))
        return result
    except IntegrityError as e:
        session.rollback()
        if ignore_duplicate:
            return None
        raise BotError(f'Alias {alias} already exists.')

async def auto_alias(session: Session, char_id: int, serial: int=None) -> List[Alias]:
    '''Automatically adds default alias. Add serial for quick adding alt character numbers.'''
    aliases = []
    for language in Language:
        name_data = await api.fetch_name(char_id, language)
        name = name_data.data.name
        if serial is not None:
            name = f'{name}{serial}'
        alias = add_alias(session, char_id, name, ignore_duplicate=True)
        if alias:
            aliases.append(alias)
        if title := name_data.data.title:
            alias_title = add_alias(session, char_id, title, ignore_duplicate=True)
            if alias_title:
                aliases.append(alias_title)

    return aliases

# transformer for id
class IdTransformer(app_commands.Transformer):
    async def transform(self, interaction: Interaction, value: str) -> int:
        try:
            id = int(value)
        except ValueError:
            with SessionAABot() as session:
                id = alias_lookup(session, value)
        return id
