from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

import api.models.mentemori as mentemori  # don't use from api.models import mentemori in case of conflict
from api.crud.mentemori import get_top_players, get_top_guilds, get_player, get_guild, get_guild_members
from api.schemas.api_models import APIResponse
from api.utils.deps import SessionDep, language_parameter
from api.utils.error import APIError

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/player/ranking',
    summary='Player Rankings',
    description='Returns player ranking data',
    response_model=APIResponse[List[mentemori.PlayerRankInfo]]
)
async def player_ranking(
    session: SessionDep,
    request: Request,
    payload: mentemori.PlayerRankingRequest = Depends()
    ):
    players = get_top_players(session, **payload.model_dump())
    return APIResponse[List[mentemori.PlayerRankInfo]].create(request, players)

@router.get(
    '/player/{player_id}',
    summary='Player',
    description='Returns player data',
    response_model=APIResponse[mentemori.PlayerDBModel]
)
async def player(
    session: SessionDep,
    request: Request,
    player_id: int
    ):
    player = get_player(session, player_id)
    if player is None:
        raise APIError(f'Player {player_id} is not in the database.')
    return APIResponse[mentemori.PlayerDBModel].create(request, player)

@router.get(
    '/guild/ranking',
    summary='Guild Rankings',
    description='Returns guild ranking data',
    response_model=APIResponse[List[mentemori.GuildRankInfo]]
)
async def guild_ranking(
    session: SessionDep,
    request: Request,
    payload: mentemori.GuildRankingRequest = Depends()
    ):
    guilds = get_top_guilds(session, **payload.model_dump())
    return APIResponse[List[mentemori.GuildRankInfo]].create(request, guilds)

@router.get(
    '/guild/{guild_id}',
    summary='Guild',
    description='Returns guild data',
    response_model=APIResponse[mentemori.GuildDBModel]
)
async def guild(
    session: SessionDep,
    request: Request,
    guild_id: int
    ):
    guild = get_guild(session, guild_id)
    if guild is None:
        raise APIError(f'Guild {guild_id} is not in the database.')
    return APIResponse[mentemori.GuildDBModel].create(request, guild)

@router.get(
    '/guild/{guild_id}/members',
    summary='Guild Members',
    description='Returns guild member data. Only returns player data existing in the database.',
    response_model=APIResponse[mentemori.GuildDBModel]
)
async def guild_member(
    session: SessionDep,
    request: Request,
    guild_id: int
    ):
    members = get_guild_members(session, guild_id)
    if not members:
        raise APIError(f'Guild {guild_id} is not in the database or no members are in the database.')
    return APIResponse[List[mentemori.PlayerDBModel]].create(request, members)
