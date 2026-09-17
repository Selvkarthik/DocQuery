import time
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.db.models import DocumentChunk
from app.services.memory import memory_service
from app.services.embedding import embedding_service
from app.schemas.health import HealthResponse, SystemInfoResponse, ServiceStatus

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Inspects PostgreSQL, pgvector extension, and Redis connectivity.",
)
def health_check(response: Response, db: Session = Depends(get_db)):
    start_time = time.time()
    db_status = ServiceStatus(status="healthy")
    redis_status = ServiceStatus(status="healthy")
    embed_status = ServiceStatus(status="healthy" if embedding_service.is_loaded() else "ready")

    # 1. Check Database & pgvector
    try:
        t0 = time.time()
        db.execute(text("SELECT 1"))
        # Check pgvector extension
        ext_check = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        has_pgvector = ext_check is not None
        db_status.latency_ms = round((time.time() - t0) * 1000, 2)
        db_status.details = {"pgvector_installed": has_pgvector}
    except Exception as e:
        db_status.status = "unhealthy"
        db_status.message = str(e)

    # 2. Check Redis
    try:
        t0 = time.time()
        redis_ok = memory_service.is_healthy()
        redis_status.latency_ms = round((time.time() - t0) * 1000, 2)
        if not redis_ok:
            redis_status.status = "degraded"
            redis_status.message = "Redis ping returned false or using fallback cache."
    except Exception as e:
        redis_status.status = "unhealthy"
        redis_status.message = str(e)

    overall_status = "healthy"
    if db_status.status == "unhealthy":
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif redis_status.status == "unhealthy" or redis_status.status == "degraded":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        embeddings=embed_status,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="System information and statistics",
    description="Returns metadata about model configurations, dimensions, and indexed document totals.",
)
def get_system_info(db: Session = Depends(get_db)):
    total_chunks = db.query(DocumentChunk).count()
    total_docs = db.query(DocumentChunk.source).distinct().count()

    return SystemInfoResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        embedding_dimension=settings.EMBEDDING_DIMENSION,
        llm_model=settings.OPENROUTER_MODEL,
        llm_base_url=settings.OPENROUTER_BASE_URL,
        total_documents=total_docs,
        total_chunks=total_chunks,
    )
