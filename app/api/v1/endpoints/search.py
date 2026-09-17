from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.retriever import retriever_service
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter(prefix="/search", tags=["Vector Search"])


@router.post(
    "",
    response_model=SearchResponse,
    summary="Direct vector semantic search",
    description="Performs pgvector cosine distance search over document embeddings without invoking the LLM generator.",
)
def semantic_search(request: SearchRequest, db: Session = Depends(get_db)):
    try:
        results = retriever_service.retrieve(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            source_filter=request.source_filter,
            db=db,
        )

        items = [
            SearchResultItem(
                source=r["source"],
                chunk_index=r["chunk_index"],
                content=r["content"],
                similarity=r["similarity"],
                distance=r["distance"],
            )
            for r in results
        ]

        return SearchResponse(
            query=request.query,
            total_results=len(items),
            results=items,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}",
        )
