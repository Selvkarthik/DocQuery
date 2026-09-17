from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DocumentSummary(BaseModel):
    source: str = Field(..., description="Filename or identifier of the document")
    chunk_count: int = Field(..., description="Total vector chunks indexed for this document")
    file_hash: str = Field(..., description="SHA-256 hash of document content")
    preview: Optional[str] = Field(default=None, description="Preview of first chunk")


class DocumentUploadResponse(BaseModel):
    source: str
    chunks_created: int
    status: str = Field(..., description="'created', 'updated', or 'unchanged'")
    message: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentSummary]
    total_documents: int
    total_chunks: int


class DocumentDeleteResponse(BaseModel):
    source: str
    chunks_deleted: int
    message: str


class IngestFolderResponse(BaseModel):
    ingested: int
    skipped: int
    total_chunks: int
    details: Dict[str, Any]
