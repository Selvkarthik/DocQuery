from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_v1_router
from app.api.v1.endpoints.health import health_check
from app.services.embedding import embedding_service
from app.services.rag_service import rag_service

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    # Warm up SentenceTransformer embedding model in background thread or eagerly
    try:
        embedding_service.encode_text("DocQuery initialization probe")
        logger.info("SentenceTransformer embedding model warmed up.")
    except Exception as e:
        logger.warning(f"Could not warm up embedding model on startup: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Enable Cross-Origin Resource Sharing (CORS)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API v1 router
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Direct /health check at root
    application.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])

    # Backward compatibility schemas & endpoint for legacy /ask
    class QuestionRequest(BaseModel):
        session_id: str = "default"
        question: str

    class Source(BaseModel):
        source: str
        chunk_index: int
        similarity: float

    class AnswerResponse(BaseModel):
        answer: str
        sources: List[Source]

    @application.post("/ask", response_model=AnswerResponse, tags=["Legacy"], summary="Legacy ask endpoint")
    def legacy_ask(request: QuestionRequest):
        result = rag_service.answer_question(
            question=request.question,
            session_id=request.session_id,
        )
        sources = [
            {
                "source": s["source"],
                "chunk_index": s["chunk_index"],
                "similarity": s["similarity"],
            }
            for s in result.get("sources", [])
        ]
        return {"answer": result["answer"], "sources": sources}

    # Mount static assets and Web UI
    if STATIC_DIR.exists():
        application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @application.get("/", include_in_schema=False)
        async def serve_ui():
            index_path = STATIC_DIR / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit /docs for Swagger API documentation."}

    return application


app = create_application()
