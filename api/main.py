import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.utils.masterdata import MasterData
from api.utils.error import APIError

from common import models  # DO NOT REMOVE, registers models for Base
from common.database import Base, engine

from api.utils.logger import get_logger
logger = get_logger(__name__)


# manually import all routers (maybe change to dynamic)
from api.routers import (
    admin, events, master, string_keys,
    character, skills,
    items, equipment,
    pve, mentemori,
)

ROUTERS = [
    admin.router, string_keys.router,
    character.router, skills.router,
    items.router, equipment.router,
    pve.router, events.router,
    mentemori.router, master.router,
]

ADMIN_USERS = [
    {"username": os.getenv('USER_AABOT'), "password": os.getenv('PASSWD_AABOT')}
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # app.state.md = MasterData()  # for testing
    app.state.md = MasterData(preload=True)
    yield


app = FastAPI(
    lifespan=lifespan,
    title='AABot API',
    version = '1.0.3',
    swagger_ui_parameters={"defaultModelsExpandDepth": -1})

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(content=exc.to_dict(), status_code=exc.status_code)

for router in ROUTERS:
    app.include_router(router)


