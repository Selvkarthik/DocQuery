"""Ingest plain-text and markdown documents into the PostgreSQL/pgvector knowledge base.

Run with ``python -m rag.ingest``
"""

import argparse
from pathlib import Path
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.ingestion import ingestion_service


def ingest_documents(document_path: Path = settings.DOCUMENTS_DIR):
    """Ingest documents from specified directory into database."""
    db = SessionLocal()
    try:
        return ingestion_service.ingest_folder(folder_path=document_path, db=db)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest text/markdown documents into the RAG database.")
    parser.add_argument("--documents", type=Path, default=settings.DOCUMENTS_DIR)
    args = parser.parse_args()
    summary = ingest_documents(args.documents)
    print("Ingestion Summary:")
    print(f" - Ingested / Updated: {summary['ingested']}")
    print(f" - Skipped (Unchanged): {summary['skipped']}")
    print(f" - Total Chunks Indexed: {summary['total_chunks']}")
