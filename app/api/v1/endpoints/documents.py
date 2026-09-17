from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ingestion import ingestion_service
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentDeleteResponse,
    IngestFolderResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload and index a document file",
    description="Uploads a plain text or markdown file, automatically chunks it, computes embeddings, and indexes into pgvector.",
)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(default=2),
    overlap: int = Form(default=1),
    db: Session = Depends(get_db),
):
    filename = file.filename or "uploaded_document.txt"
    if not filename.endswith((".txt", ".md", ".csv", ".log")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently supported file formats are: .txt, .md, .csv, .log",
        )

    try:
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8", errors="ignore")

        result = ingestion_service.ingest_text_content(
            source_name=filename,
            text_content=text_content,
            db=db,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        return DocumentUploadResponse(
            source=result["source"],
            chunks_created=result["chunks_created"],
            status=result["status"],
            message=result["message"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest uploaded document: {str(e)}",
        )


@router.post(
    "/ingest-folder",
    response_model=IngestFolderResponse,
    summary="Ingest documents from local directory",
    description="Scans the documents directory and indexes any new or updated text/markdown files.",
)
def ingest_folder(db: Session = Depends(get_db)):
    try:
        summary = ingestion_service.ingest_folder(db=db)
        return IngestFolderResponse(
            ingested=summary["ingested"],
            skipped=summary["skipped"],
            total_chunks=summary["total_chunks"],
            details=summary["details"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Folder ingestion failed: {str(e)}",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all indexed documents",
    description="Returns metadata, chunk counts, and SHA-256 hashes for all documents indexed in pgvector.",
)
def list_documents(db: Session = Depends(get_db)):
    docs = ingestion_service.list_documents(db=db)
    summaries = [
        DocumentSummary(
            source=d["source"],
            chunk_count=d["chunk_count"],
            file_hash=d["file_hash"],
            preview=d.get("preview"),
        )
        for d in docs
    ]
    total_chunks = sum(d["chunk_count"] for d in docs)
    return DocumentListResponse(
        documents=summaries,
        total_documents=len(summaries),
        total_chunks=total_chunks,
    )


@router.delete(
    "/{source_name}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document from index",
    description="Removes all vector chunks associated with the given document source name.",
)
def delete_document(source_name: str, db: Session = Depends(get_db)):
    deleted_count = ingestion_service.delete_document(source_name=source_name, db=db)
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No document chunks found for source '{source_name}'.",
        )
    return DocumentDeleteResponse(
        source=source_name,
        chunks_deleted=deleted_count,
        message=f"Successfully deleted {deleted_count} chunks for '{source_name}'.",
    )
