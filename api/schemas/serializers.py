from pydantic import FieldSerializationInfo

import api.utils.enums as enums
from api.crud.string_keys import read_string_key_language

from api.utils.logger import get_logger
logger = get_logger(__name__)

def serialize_str(v: str | enums._Enum | enums._Flag, info: FieldSerializationInfo):
    '''
    Translates string keys into their language.
    Returns input string if not a key format: '[Key]'
    
    '''
    context = info.context
    if v and isinstance(context, dict):
        language = context.get('language', enums.Language.enus)
        session = context.get('db', None)
        nullable = context.get('nullable', False)

        if isinstance(v, enums._Enum):
            s = [v.str_key]
        elif isinstance(v, enums._Flag):
            s = v.str_keys
        elif isinstance(v, str):
            s = [v]
        else:
            raise ValueError(f'Cannot serialize string from: {v}')

        results = []
        for key in s:
            if key.startswith('[') and key.endswith(']'):
                if session is None:
                    raise ValueError('DB session could not be found')
                result = read_string_key_language(session, key, language)
                if nullable and result is None:  # stella's case ([CharacterProfileVocalUS57])
                    return None
                results.append(result)
            else:
                results.append(key)  # not a string key, return text
        return str.join('|', results)

    else:  # No context = raw data
        return v

    

def serialize_enum(v: enums.Enum | enums.Flag, info: FieldSerializationInfo):
    context = info.context
    if isinstance(context, dict):
        if isinstance(v, enums.IntFlag) and v == 0:
            return None  # UW Rarity
        s = v.name
        if isinstance(s, str):
            s = s.replace('Plus', '+')  # char rarity etc
        if s == 'None_':  # Enum value 0 remove _ (case: Passive Trigger, Voiceline Unlock)
            return None
        return s
    else:
        return v.value
        