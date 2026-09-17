from pydantic import BaseModel, Field
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Semantic search query")
    top_k: Optional[int] = Field(default=None, ge=1, le=50, description="Max results to retrieve")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Cosine similarity cutoff")
    source_filter: Optional[str] = Field(default=None, description="Filter matches by specific document source name")


class SearchResultItem(BaseModel):
    source: str
    chunk_index: int
    content: str
    similarity: float
    distance: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
