from fastapi import Query
from pydantic import BaseModel, Field, TypeAdapter
from typing import List

from api.utils import enums, timezones
from api.utils.masterdata import MasterData
from api.utils.error import APIError

class GrandBattleDate(BaseModel):
    start: str = Field(..., validation_alias='StartTime')
    end: str = Field(..., validation_alias='EndTime')

class Group(BaseModel):
    group_id: int = Field(..., validation_alias='Id')
    server: enums.Server = Field(..., validation_alias='TimeServerId')
    start: str = Field(..., validation_alias='StartTime')
    end: str = Field(..., validation_alias='EndTime')
    worlds: List[int] = Field(..., validation_alias='WorldIdList')
    grand_battle: List[GrandBattleDate] = Field(..., validation_alias='GrandBattleDateTimeList')
    league_start: str = Field(..., validation_alias='StartLegendLeagueDateTime')
    league_end: str = Field(..., validation_alias='EndLegendLeagueDateTime')
    
    class Config:
        populate_by_name = True

Groups = TypeAdapter(List[Group])

async def get_groups(md: MasterData, is_active=True):
    '''Just use mentemori instead unless all data is needed'''
    group_data = await md.get_MB('WorldGroupMB')
    groups = Groups.validate_python(group_data)
    if is_active:
        new_groups = []
        for group in groups:
            server = group.server
            if timezones.is_active(group.start, group.end, server):
                new_groups.append(group)
        groups = new_groups
        
    return groups
            