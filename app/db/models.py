from sqlalchemy import Column, Integer, Text, String, Index
from sqlalchemy.orm import DeclarativeBase
from pgvector.sqlalchemy import Vector
from app.core.config import settings


class Base(DeclarativeBase):
    pass


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    source = Column(Text, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION))
    file_hash = Column(String(64), nullable=False, index=True)

    __table_args__ = (
        Index("idx_docchunks_source_index", "source", "chunk_index"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "file_hash": self.file_hash,
        }

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, source='{self.source}', chunk_index={self.chunk_index})>"
