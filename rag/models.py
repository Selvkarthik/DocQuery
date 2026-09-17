"""SQLAlchemy models adapter for backward compatibility."""

from app.db.models import Base, DocumentChunk

__all__ = ["Base", "DocumentChunk"]