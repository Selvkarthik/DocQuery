from sentence_transformers import SentenceTransformer
from database import SessionLocal
from models import DocumentChunk
import re
from pathlib import Path

document_path = Path('./documents')
files = list(document_path.glob('*.txt'))

model = SentenceTransformer('all-MiniLM-L6-v2')

chunk_size = 2
overlap = 1

def chunk_text(sentences, chunk_size, overlap):
    chunks = []
    for start in range(0, len(sentences), chunk_size-overlap):
        chunks.append(' '.join(sentences[start : start + chunk_size]))
    return chunks

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    sentences = re.split(r'(?<=[?!.])\s+', text)

    data = chunk_text(sentences, chunk_size, overlap)
    embeddings = model.encode(data)

    db = SessionLocal()
    try:
        for index, (chunk, embedding) in enumerate(zip(data, embeddings)):
            document = DocumentChunk(
                content = chunk,
                source = file_path.name,
                chunk_index = index,
                embedding = embedding.tolist()
            )
            db.add(document)
        db.commit()
    finally:
        db.close()