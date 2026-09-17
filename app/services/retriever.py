from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.services.embedding import embedding_service


class VectorRetrieverService:
    def __init__(self):
        self.embedding_service = embedding_service

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        source_filter: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve most semantically similar document chunks from pgvector."""
        clean_query = query.strip()
        if not clean_query:
            return []

        k = top_k or settings.DEFAULT_TOP_K
        threshold = similarity_threshold if similarity_threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD

        query_embedding = self.embedding_service.encode_text(clean_query)
        embedding_str = str(query_embedding)

        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            where_clauses = ["1=1"]
            params: Dict[str, Any] = {
                "query_embedding": embedding_str,
                "top_k": k,
            }

            if source_filter:
                where_clauses.append("source = :source_filter")
                params["source_filter"] = source_filter

            sql = f"""
                SELECT 
                    content, 
                    source, 
                    chunk_index,
                    embedding <=> CAST(:query_embedding AS vector) AS distance
                FROM document_chunks
                WHERE {" AND ".join(where_clauses)}
                ORDER BY embedding <=> CAST(:query_embedding AS vector) ASC
                LIMIT :top_k
            """

            result = db.execute(text(sql), params)
            sources: List[Dict[str, Any]] = []

            for row in result:
                distance = float(row[3])
                similarity = max(0.0, min(1.0, 1.0 - distance))

                if similarity >= threshold:
                    sources.append({
                        "content": row[0],
                        "source": row[1],
                        "chunk_index": int(row[2]),
                        "distance": round(distance, 4),
                        "similarity": round(similarity, 4),
                    })

            return sources

        except Exception as e:
            logger.error(f"Error during vector retrieval: {e}")
            raise
        finally:
            if should_close:
                db.close()


retriever_service = VectorRetrieverService()
