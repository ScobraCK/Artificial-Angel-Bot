from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.mentemori import get_top_players, get_top_guilds, get_player, get_guild, get_guild_members
from common.schemas import APIResponse
from api.schemas.requests import PlayerRankingRequest, GuildRankingRequest
from api.utils.deps import SessionDep
from api.utils.error import APIError
from common import schemas

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/player/ranking',
    summary='Player Rankings',
    description='Returns player ranking data. Data is collected from mentemori.icu rankings.',
    response_model=APIResponse[list[schemas.PlayerRankInfo]]
)
async def player_ranking(
    session: SessionDep,
    request: Request,
    payload: PlayerRankingRequest = Depends()
    ):
    players = await get_top_players(session, **payload.model_dump())
    return APIResponse[list[schemas.PlayerRankInfo]].create(request, players)

@router.get(
    '/player/{player_id}',
    summary='Player',
    description='Returns player data. Data is collected from mentemori.icu rankings and may have missing or outdated data for players not in the rankings.',
    response_model=APIResponse[schemas.Player]
)
async def player(
    session: SessionDep,
    request: Request,
    player_id: int
    ):
    player = await get_player(session, player_id)
    if player is None:
        raise APIError(f'Player {player_id} is not in the database.')
    return APIResponse[schemas.Player].create(request, player)

@router.get(
    '/guild/ranking',
    summary='Guild Rankings',
    description='Returns guild ranking data. Data is collected from mentemori.icu rankings.',
    response_model=APIResponse[list[schemas.GuildRankInfo]]
)
async def guild_ranking(
    session: SessionDep,
    request: Request,
    payload: GuildRankingRequest = Depends()
    ):
    guilds = await get_top_guilds(session, **payload.model_dump())
    return APIResponse[list[schemas.GuildRankInfo]].create(request, guilds)

@router.get(
    '/guild/{guild_id}',
    summary='Guild',
    description='Returns guild data. Data is collected from mentemori.icu rankings and may have missing or outdated data for players not in the rankings.',
    response_model=APIResponse[list[schemas.Player]]
)
async def guild(
    session: SessionDep,
    request: Request,
    guild_id: int
    ):
    guild = await get_guild(session, guild_id)
    if guild is None:
        raise APIError(f'Guild {guild_id} is not in the database.')
    return APIResponse[schemas.Guild].create(request, guild)

@router.get(
    '/guild/{guild_id}/members',
    summary='Guild Members',
    description='Returns guild member data. Only returns player data existing in the database. Data is collected from mentemori.icu rankings and may have missing or outdated data for players not in the rankings.',
    response_model=APIResponse[list[schemas.Player]]
)
async def guild_members(
    session: SessionDep,
    request: Request,
    guild_id: int
    ):
    members = await get_guild_members(session, guild_id)
    if not members:
        raise APIError(f'Guild {guild_id} is not in the database or no members are in the database.')
    return APIResponse[list[schemas.Player]].create(request, members)
