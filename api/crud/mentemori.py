from sqlalchemy import select, desc
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional, List

from common.models import PlayerORM, GuildORM, PlayerColumns

from api.utils.logger import get_logger
logger = get_logger(__name__)

async def update_players(session: AsyncSession, player_data: dict):
    timestamp = player_data["timestamp"]

    for world in player_data["data"]:
        world_id = world["world_id"]
        player_info = world["player_info"]

        bp_ranking = {p["id"]: p["bp"] for p in world["rankings"]["bp"]}
        azure_ranking = {p["id"]: p["tower_id"] for p in world["rankings"]["tower_blue"]}
        crimson_ranking = {p["id"]: p["tower_id"] for p in world["rankings"]["tower_red"]}
        emerald_ranking = {p["id"]: p["tower_id"] for p in world["rankings"]["tower_green"]}
        amber_ranking = {p["id"]: p["tower_id"] for p in world["rankings"]["tower_yellow"]}

        update_list = []
        for player_id, player in player_info.items():
            player_id = int(player_id)
            update_data = {
                "id": player_id,
                "world_id": world_id,
                "name": player["name"],
                "bp": player["bp"],
                "rank": player["rank"],
                "quest_id": player["quest_id"],
                "tower_id": player["tower_id"],
                "azure_tower_id": azure_ranking.get(player_id),
                "crimson_tower_id": crimson_ranking.get(player_id),
                "emerald_tower_id": emerald_ranking.get(player_id),
                "amber_tower_id": amber_ranking.get(player_id),
                "icon_id": player["icon_id"],
                "guild_id": player["guild_id"],
                "guild_join_time": player["guild_join_time"],
                "guild_position": player["guild_position"],
                "prev_legend_league_class": player["prev_legend_league_class"],
                "timestamp": timestamp
            }
            # Used to be inconsistent, this is a check
            if bp_ranking.get(player_id) and player["bp"] != bp_ranking.get(player_id):
                logger.error(f"Player {player['name']} has inconsistent BP data: {player['bp']} vs {bp_ranking.get(player_id)}")
            update_list.append(update_data)
        stmt = insert(PlayerORM).values(update_list)
        update_dict = {
            c.name: getattr(stmt.excluded, c.name) 
            for c in PlayerORM.__table__.columns 
            if c.name != 'id'
            }
        stmt = stmt.on_conflict_do_update(index_elements=['id'], set_=update_dict)
        await session.execute(stmt)

    await session.commit()

async def update_guilds(session: AsyncSession, guild_data: dict):
    timestamp = guild_data["timestamp"]

    for world in guild_data["data"]:
        world_id = world["world_id"]
        guild_info = world["guild_info"]

        update_list = []
        for guild_id, guild in guild_info.items():
            guild_id = int(guild_id)
            update_data = {
                "id": guild_id,
                "world_id": world_id,
                "name": guild["name"],
                "bp": guild["bp"],
                "level": guild["level"],
                "stock": guild["stock"],
                "exp": guild["exp"],
                "num_members": guild["num_members"],
                "leader_id": guild["leader_id"],
                "description": guild["description"],
                "free_join": guild["free_join"],
                "bp_requirement": guild["bp_requirement"],
                "timestamp": timestamp
            }
            update_list.append(update_data)
        stmt = insert(GuildORM).values(update_list)
        update_dict = {
            c.name: getattr(stmt.excluded, c.name) 
            for c in GuildORM.__table__.columns 
            if c.name != 'id'
            }
        stmt = stmt.on_conflict_do_update(index_elements=['id'], set_=update_dict)
        await session.execute(stmt)

    await session.commit()

async def get_top_players(
    session: AsyncSession,
    count: int,
    order_by: PlayerColumns,
    world_id: Optional[List[int]] = None,
    server: Optional[int] = None,
):
    valid_columns: Dict[str, InstrumentedAttribute] = {
        "bp": PlayerORM.bp,
        "rank": PlayerORM.rank,
        "quest": PlayerORM.quest_id,
        "tower": PlayerORM.tower_id,
        "azure_tower": PlayerORM.azure_tower_id,
        "crimson_tower": PlayerORM.crimson_tower_id,
        "emerald_tower": PlayerORM.emerald_tower_id,
        "amber_tower": PlayerORM.amber_tower_id
    }

    stmt = select(
        PlayerORM.name,
        PlayerORM.server,
        PlayerORM.world,
        PlayerORM.bp,
        PlayerORM.rank,
        PlayerORM.quest_id,
        PlayerORM.tower_id,
        PlayerORM.azure_tower_id,
        PlayerORM.crimson_tower_id,
        PlayerORM.emerald_tower_id,
        PlayerORM.amber_tower_id,
        PlayerORM.timestamp
    )

    if world_id:
        stmt = stmt.where(PlayerORM.world_id.in_(world_id))
    elif server:
        stmt = stmt.where(PlayerORM.server == server)

    stmt = stmt.where(valid_columns[order_by].isnot(None))  # Exclude NULLs
    stmt = stmt.order_by(desc(valid_columns[order_by])).limit(count)

    result = await session.execute(stmt)
    return result.all()

async def get_top_guilds(
    session: AsyncSession,
    count: int,
    world_id: Optional[List[int]] = None,
    server: Optional[int] = None,
):
    stmt = select(
        GuildORM.name,
        GuildORM.server,
        GuildORM.world,
        GuildORM.bp,
        GuildORM.timestamp
    )

    if world_id:
        stmt = stmt.where(GuildORM.world_id.in_(world_id))
    elif server:
        stmt = stmt.where(GuildORM.server == server)

    stmt = stmt.order_by(desc(GuildORM.bp)).limit(count)

    result = await session.execute(stmt)
    return result.all()

async def get_player(session: AsyncSession, player_id: int):
    stmt = select(PlayerORM).where(PlayerORM.id == player_id)
    result = await session.execute(stmt)
    return result.fetchone()

async def get_guild(session: AsyncSession, guild_id: int):
    stmt = select(GuildORM).where(GuildORM.id == guild_id)
    result = await session.execute(stmt)
    return result.fetchone()

async def get_guild_members(session: AsyncSession, guild_id: int):
    '''Only shows members in the DB'''
    stmt = select(PlayerORM).where(PlayerORM.guild_id == guild_id)
    result = await session.execute(stmt)
    return result.all()