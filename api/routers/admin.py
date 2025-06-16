import os

from fastapi import APIRouter, HTTPException, Request, Response
from httpx import AsyncClient

from api.crud.character import upsert_chars
from api.crud.mentemori import update_guilds, update_players
from api.crud.string_keys import update_and_log_strings
from api.utils import mentemori
from api.utils.deps import SessionDep
from api.utils.error import MentemoriError
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

router = APIRouter(include_in_schema=False)

@router.get('/admin/update')
async def update_master(key: str, session: SessionDep, request: Request):
    '''Call only if master data had an update'''
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    md: MasterData = request.app.state.md
    try:
        updated = await md.update_version()
        await update_and_log_strings(session, md, updated)
        
        if not updated:
            return Response(status_code=204)

        if md.version is None or not md.catalog:  # In case MasterData is not initialized
            updated = await md._preload()

        inserted_ids = []
        if 'CharacterMB' in updated:
            inserted_ids = await upsert_chars(session, md)
            if inserted_ids is None:
                raise HTTPException(status_code=500, detail='Failed to update characters.')
            
        files_updated = '\n'.join(updated)
        characters_added = inserted_ids if inserted_ids else 'None'
        embed = {
            "title": "🔄 Master Update",
            "description": f"**Master version**: {md.version}\n**Files Updated**\n```\n{files_updated}```\n**Characters Added\n**```\n{characters_added}```",
            "color": 0x2ecc71
        }
        async with AsyncClient() as client:
            await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        return Response(status_code=204)
        
    except Exception as e:
        logger.error(f"Error updating master data: {str(e)}")
        raise HTTPException(status_code=500, detail='Failed to update master data.')

@router.get('/admin/update/strings')
async def update_strings(key: str, session: SessionDep, request: Request):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    md: MasterData = request.app.state.md
    await update_and_log_strings(session, md)
    
    embed = {
        "title": "🔄 Manual Update",
        "description": f"**Master version**: {md.version}\n**String update triggered**",
        "color": 0x2ecc71
    }
    async with AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})

    return Response(status_code=204)

@router.get('/admin/update/characters')
async def update_chars(key: str, session: SessionDep, request: Request):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    md: MasterData = request.app.state.md
    inserted_ids = await upsert_chars(session, md)
    if inserted_ids is None:
        raise HTTPException(status_code=500, detail='Failed to update characters.')
    
    characters_added = inserted_ids if inserted_ids else 'None' 
    embed = {
        "title": "🔄 Manual Update",
        "description": f"**Master version**: {md.version}\n**Characters Added\n**```{characters_added}```",
        "color": 0x2ecc71
    }
    async with AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    
    return {'new': inserted_ids}  # TODO: triger alias update

@router.get('/admin/mentemori')
async def update_mentemori(key: str, session: SessionDep):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        players = await mentemori.fetch_mentemori(mentemori.PLAYER)
        await update_players(session, players)
        guilds = await mentemori.fetch_mentemori(mentemori.GUILD)
        await update_guilds(session, guilds)
        return Response(status_code=204)
    except MentemoriError as e:
        return {'detail': e.response}
    except Exception as e:
        logger.error(str(e))
        raise e

@router.get('/admin/mentemori/players')
async def update_mentemori_players(key: str, session: SessionDep):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        players = await mentemori.fetch_mentemori(mentemori.PLAYER)
        await update_players(session, players)
        return Response(status_code=204)
    except MentemoriError as e:
        return {'detail': e.response}
    except Exception as e:
        logger.error(str(e))
        raise e
    
@router.get('/admin/mentemori/guilds')
async def update_mentemori_guilds(key: str, session: SessionDep):
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        guilds = await mentemori.fetch_mentemori(mentemori.GUILD)
        await update_guilds(session, guilds)
        return Response(status_code=204)
    except MentemoriError as e:
        return {'detail': e.response}
    except Exception as e:
        logger.error(str(e))
        raise e
    