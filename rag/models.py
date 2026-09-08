from sqlalchemy import Column, Integer, Text, String
from sqlalchemy.orm import DeclarativeBase
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384))
    file_hash = Column(String(64), nullable=False)