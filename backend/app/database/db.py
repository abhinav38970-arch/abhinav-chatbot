from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float, JSON,
    Index, UniqueConstraint, ForeignKey, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'school_data.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    # WAL journal = safe incremental commits during long crawls + much faster writes at 150k-page scale
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def init_db():
    """
    Creates database tables if they do not exist.
    Safe to run multiple times.
    """
    from . import models  # noqa: F401 — registers models on Base before create_all
    Base.metadata.create_all(bind=engine)


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()
