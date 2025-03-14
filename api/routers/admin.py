from fastapi import APIRouter, HTTPException, Request, Response
import os

from api.crud.character import upsert_chars
from api.crud.mentemori import update_guilds, update_players
from api.crud.string_keys import update_and_log_strings
from api.utils import mentemori
from api.utils.deps import SessionDep
from api.utils.error import MentemoriError
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter(include_in_schema=False)

@router.get('/admin/update')
async def update_master(key: str, session: SessionDep, request: Request):
    '''Call only if master data had an update'''
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    md: MasterData = request.app.state.md

    updated = await md.update_version()
    await update_and_log_strings(session, md, updated)

    if md.version is None or not md.catalog:  # In case MasterData is not initialized
        updated = await md._preload()

    inserted_ids = None
    if 'CharacterMB' in updated:
        inserted_ids = await upsert_chars(session, md)

    return {'data': updated, 'new_chars': inserted_ids}

@router.get('/admin/update/strings')
async def update_strings(key: str, session: SessionDep, request: Request):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    md: MasterData = request.app.state.md
    await update_and_log_strings(session, md)

    return Response(status_code=204)

@router.get('/admin/update/characters')
async def update_chars(key: str, session: SessionDep, request: Request):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    md: MasterData = request.app.state.md
    inserted_ids = await upsert_chars(session, md)

    return {'new': inserted_ids}

@router.get('/admin/mentemori')
async def update_mentemori(key: str, session: SessionDep):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        players = await mentemori.fetch_mentemori(mentemori.PLAYER)
        update_players(session, players)
        guilds = await mentemori.fetch_mentemori(mentemori.GUILD)
        update_guilds(session, guilds)
        return Response(status_code=204)
    except MentemoriError as e:
        return {'error': e.response}
    except Exception as e:
        logger.error(str(e))
        raise e

@router.get('/admin/mentemori/players')
async def update_mentemori_players(key: str, session: SessionDep):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        players = await mentemori.fetch_mentemori(mentemori.PLAYER)
        update_players(session, players)
        return Response(status_code=204)
    except MentemoriError as e:
        return {'error': e.response}
    except Exception as e:
        logger.error(str(e))
        raise e
    
@router.get('/admin/mentemori/guilds')
async def update_mentemori_guilds(key: str, session: SessionDep):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        guilds = await mentemori.fetch_mentemori(mentemori.GUILD)
        update_guilds(session, guilds)
        return Response(status_code=204)
    except MentemoriError as e:
        return {'error': e.response}
    except Exception as e:
        logger.error(str(e))
        raise e
    