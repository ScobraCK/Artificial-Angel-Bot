from common import timezones
from api.utils.masterdata import MasterData
from common import schemas

async def get_groups(md: MasterData, is_active=True):
    '''Just use mentemori instead unless all data is needed'''
    group_data = await md.get_MB('WorldGroupMB')
    groups = schemas.Groups.validate_python(group_data)
    if is_active:
        new_groups = []
        for group in groups:
            server = group.server
            if timezones.check_active(group.start, group.end, server):
                new_groups.append(group)
        groups = new_groups
        
    return groups
            