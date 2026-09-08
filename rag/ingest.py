from sentence_transformers import SentenceTransformer
from rag.database import SessionLocal
from rag.models import DocumentChunk
import re
from pathlib import Path
import hashlib

document_path = Path('./documents')
files = list(document_path.glob('*.txt'))

def get_file_hash(file_path):
    with open(file_path, 'rb') as file:
        return hashlib.sha256(file.read()).hexdigest()

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

    file_hash = get_file_hash(file_path)

    db = SessionLocal()
    try:
        existing_file = db.query(DocumentChunk).filter(DocumentChunk.source == file_path.name).first()
        if existing_file:
            if existing_file.file_hash == file_hash:
                print(f"Skipping {file_path.name} - Already Ingested")
                continue

            print(f"{file_path.name} changed - re ingesting")
            db.query(DocumentChunk).filter(DocumentChunk.source == file_path.name).delete()


        print(f"Ingesting {file_path.name}...")

        sentences = re.split(r'(?<=[?!.])\s+', text)
        data = chunk_text(sentences, chunk_size, overlap)
        embeddings = model.encode(data)

        for index, (chunk, embedding) in enumerate(zip(data, embeddings)):
            document = DocumentChunk(
                content = chunk,
                source = file_path.name,
                chunk_index = index,
                embedding = embedding.tolist(),
                file_hash = file_hash
            )
            db.add(document)
        db.commit()
    finally:
        db.close()