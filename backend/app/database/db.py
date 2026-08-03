from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///database/school_data.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
# ✅ ensure all models are registered before table creation
from . import models  # DO NOT REMOVE

def init_db():
    """
    Creates database tables if they do not exist.
    Safe to run multiple times.
    """
    Base.metadata.create_all(bind=engine)
