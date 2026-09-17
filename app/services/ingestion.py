import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.models import DocumentChunk
from app.services.embedding import embedding_service


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def chunk_sentences(sentences: List[str], chunk_size: int = 2, overlap: int = 1) -> List[str]:
    """Group sentences into overlapping chunks."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and strictly smaller than chunk_size")

    step = max(1, chunk_size - overlap)
    chunks = []
    i = 0
    while i < len(sentences):
        slice_items = sentences[i : i + chunk_size]
        if slice_items:
            chunks.append(" ".join(slice_items))
        if i + chunk_size >= len(sentences):
            break
        i += step
    return chunks


def split_text_into_chunks(text: str, chunk_size: int = 2, overlap: int = 1) -> List[str]:
    """Split text into sentences and chunk them."""
    cleaned = text.strip()
    if not cleaned:
        return []

    # Split by standard sentence terminators (. ! ?)
    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    # If text doesn't contain standard sentence punctuation (e.g. bullet points or single paragraphs)
    if len(sentences) <= 1:
        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            sentences = paragraphs
        else:
            lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
            if len(lines) > 1:
                sentences = lines

    if not sentences:
        return [cleaned]

    return chunk_sentences(sentences, chunk_size, overlap)


class IngestionService:
    def __init__(self):
        self.embedding_service = embedding_service

    def ingest_text_content(
        self,
        source_name: str,
        text_content: str,
        db: Session,
        chunk_size: int = 2,
        overlap: int = 1,
    ) -> Dict[str, Any]:
        """Index text content into pgvector with SHA-256 deduplication."""
        raw_bytes = text_content.encode("utf-8")
        file_hash = compute_sha256(raw_bytes)

        existing = db.query(DocumentChunk).filter(DocumentChunk.source == source_name).first()
        if existing and existing.file_hash == file_hash:
            logger.info(f"Document '{source_name}' is unchanged (hash={file_hash[:8]}). Skipping.")
            total_existing = db.query(DocumentChunk).filter(DocumentChunk.source == source_name).count()
            return {
                "source": source_name,
                "status": "unchanged",
                "chunks_created": total_existing,
                "message": f"Document '{source_name}' is already up to date.",
            }

        status = "updated" if existing else "created"
        if existing:
            deleted_count = db.query(DocumentChunk).filter(DocumentChunk.source == source_name).delete()
            logger.info(f"Removed {deleted_count} existing chunks for '{source_name}' before re-ingestion.")

        chunks = split_text_into_chunks(text_content, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return {
                "source": source_name,
                "status": "empty",
                "chunks_created": 0,
                "message": "Document contains no readable content.",
            }

        logger.info(f"Generating embeddings for {len(chunks)} chunks in '{source_name}'...")
        embeddings = self.embedding_service.encode_batch(chunks)

        for index, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            doc = DocumentChunk(
                content=chunk,
                source=source_name,
                chunk_index=index,
                embedding=emb,
                file_hash=file_hash,
            )
            db.add(doc)

        db.commit()
        logger.info(f"Successfully indexed '{source_name}' ({len(chunks)} chunks).")

        return {
            "source": source_name,
            "status": status,
            "chunks_created": len(chunks),
            "message": f"Successfully indexed '{source_name}' ({len(chunks)} chunks).",
        }

    def ingest_file(self, file_path: Path, db: Session) -> Dict[str, Any]:
        """Ingest a single file from disk."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return self.ingest_text_content(
            source_name=file_path.name,
            text_content=content,
            db=db,
        )

    def ingest_folder(self, folder_path: Optional[Path] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """Ingest all .txt and .md files in the documents directory."""
        target_dir = folder_path or settings.DOCUMENTS_DIR
        if not target_dir.exists():
            raise FileNotFoundError(f"Directory not found: {target_dir}")

        files = sorted(list(target_dir.glob("*.txt")) + list(target_dir.glob("*.md")))
        if not files:
            return {"ingested": 0, "skipped": 0, "total_chunks": 0, "details": {}}

        summary = {"ingested": 0, "skipped": 0, "total_chunks": 0, "details": {}}

        for f in files:
            try:
                res = self.ingest_file(f, db=db)
                summary["details"][f.name] = res
                if res["status"] in ("created", "updated"):
                    summary["ingested"] += 1
                    summary["total_chunks"] += res["chunks_created"]
                elif res["status"] == "unchanged":
                    summary["skipped"] += 1
            except Exception as e:
                logger.error(f"Error ingesting file {f.name}: {e}")
                summary["details"][f.name] = {"status": "error", "message": str(e)}

        return summary

    def list_documents(self, db: Session) -> List[Dict[str, Any]]:
        """List distinct documents indexed in the system."""
        rows = (
            db.query(
                DocumentChunk.source,
                DocumentChunk.file_hash,
                func.count(DocumentChunk.id).label("chunk_count"),
                func.min(DocumentChunk.content).label("preview"),
            )
            .group_by(DocumentChunk.source, DocumentChunk.file_hash)
            .all()
        )

        return [
            {
                "source": r[0],
                "file_hash": r[1],
                "chunk_count": int(r[2]),
                "preview": r[3][:150] + "..." if r[3] and len(r[3]) > 150 else r[3],
            }
            for r in rows
        ]

    def delete_document(self, source_name: str, db: Session) -> int:
        """Delete all chunks for a document source."""
        count = db.query(DocumentChunk).filter(DocumentChunk.source == source_name).delete()
        db.commit()
        logger.info(f"Deleted {count} chunks for source '{source_name}'.")
        return count


ingestion_service = IngestionService()
