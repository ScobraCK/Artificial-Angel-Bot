import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
DATABASE_URL = f'postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres/{POSTGRES_DB}'

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
