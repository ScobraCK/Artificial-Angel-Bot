import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

import api.models  # DO NOT REMOVE, registers models for Base

from api.database import Base, engine
from api.utils.masterdata import MasterData
from api.utils.error import APIError

from api.utils.logger import get_logger
logger = get_logger(__name__)


# manually import all routers (maybe change to dynamic)
from api.routers import (
    admin, string_keys,
    character, skills,
    items, equipment,
    pve, events,
    mentemori,raw,
)

ROUTERS = [
    admin.router, string_keys.router,
    character.router, skills.router,
    items.router, equipment.router,
    pve.router, events.router,
    mentemori.router, raw.router,
]

ADMIN_USERS = [
    {"username": os.getenv('USER_AABOT'), "password": os.getenv('PASSWD_AABOT')}
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # app.state.md = MasterData()  # for testing
    app.state.md = MasterData(preload=True)
    yield


app = FastAPI(
    lifespan=lifespan,
    title='AABot API',
    version = '1.0.0',
    swagger_ui_parameters={"defaultModelsExpandDepth": -1})

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(content=exc.to_dict(), status_code=exc.status_code)

for router in ROUTERS:
    app.include_router(router)


