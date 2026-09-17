from pydantic import BaseModel
from typing import Optional, Dict, Any


class ServiceStatus(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    database: ServiceStatus
    redis: ServiceStatus
    embeddings: ServiceStatus
    timestamp: str


class SystemInfoResponse(BaseModel):
    project_name: str
    version: str
    description: str
    embedding_model: str
    embedding_dimension: int
    llm_model: str
    llm_base_url: str
    total_documents: int
    total_chunks: int
