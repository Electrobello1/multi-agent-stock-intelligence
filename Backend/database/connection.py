import os

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


DB_POOL_SIZE = int(
    os.getenv(
        "DB_POOL_SIZE",
        "15"
    )
)

DB_MAX_OVERFLOW = int(
    os.getenv(
        "DB_MAX_OVERFLOW",
        "15"
    )
)

DB_POOL_TIMEOUT = int(
    os.getenv(
        "DB_POOL_TIMEOUT",
        "30"
    )
)

DB_POOL_RECYCLE = int(
    os.getenv(
        "DB_POOL_RECYCLE",
        "1800"
    )
)


engine = create_engine(
    DATABASE_URL,

    pool_size=DB_POOL_SIZE,

    max_overflow=DB_MAX_OVERFLOW,

    pool_timeout=DB_POOL_TIMEOUT,

    pool_recycle=DB_POOL_RECYCLE,

    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()