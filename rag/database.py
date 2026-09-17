"""Database connection adapter for backward compatibility."""

from sqlalchemy import make_url
from app.core.config import settings
from app.db.session import engine, SessionLocal

DB_URL = make_url(settings.database_url)

__all__ = ["engine", "SessionLocal", "DB_URL"]
