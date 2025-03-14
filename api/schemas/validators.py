from pydantic import ValidationInfo

import api.utils.timezones as timezones
import api.utils.enums as enums

def val_date_jst(v: str):
    if isinstance(v, int):
        return v
    return timezones.convert_from_jst(v)

def val_date_local(v: str, info: ValidationInfo):
    '''Must have a server: enums.Server defined befoer to use'''
    if isinstance(v, int):
        return v
    return timezones.convert_from_local(v, info.data['server'])
