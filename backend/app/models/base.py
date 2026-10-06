"""
SQLAlchemy declarative base and shared utilities.
All models import from here to ensure a single metadata registry.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
