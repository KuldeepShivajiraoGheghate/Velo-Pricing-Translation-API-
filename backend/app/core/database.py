"""
Database session factory and engine setup.
Uses SQLAlchemy 2.0 async-compatible Session.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.settings import get_settings


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,       # verify connection liveness on checkout
        pool_size=10,
        max_overflow=20,
        echo=(settings.app_env == "local"),  # SQL query logging in local only
    )


engine = get_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session and closes it on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
