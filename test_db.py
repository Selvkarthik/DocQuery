from rag.database import SessionLocal
from rag.models import DocumentChunk

db = SessionLocal()

try:
    chunks = db.query(DocumentChunk).all()
    for chunk in chunks:
        print(chunk.id, chunk.content, chunk.source, chunk.chunk_index)
finally:
    db.close()