import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
DATABASE_URL = f'postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres/{POSTGRES_DB}'

class Base(DeclarativeBase):
    pass

engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
