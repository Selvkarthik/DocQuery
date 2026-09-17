from typing import Dict, Any, List, Optional, Generator
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.services.retriever import retriever_service
from app.services.generator import generator_service
from app.services.memory import memory_service


class RAGService:
    def __init__(self):
        self.retriever = retriever_service
        self.generator = generator_service
        self.memory = memory_service

    def answer_question(
        self,
        question: str,
        session_id: str = "default",
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Execute full conversational RAG pipeline with session memory."""
        k = top_k or settings.DEFAULT_TOP_K
        threshold = similarity_threshold if similarity_threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD

        # 1. Load prior conversation history
        history = self.memory.load_messages(session_id, limit=settings.MAX_HISTORY_TURNS * 2)

        # 2. Retrieve grounded document chunks
        sources = self.retriever.retrieve(
            query=question,
            top_k=k,
            similarity_threshold=threshold,
            db=db,
        )

        # 3. Handle case where no relevant chunks are found
        if not sources:
            fallback_answer = "I do not have enough information in the provided documents to answer that question."
            self.memory.add_turn(session_id, question, fallback_answer)
            return {
                "answer": fallback_answer,
                "session_id": session_id,
                "question": question,
                "sources": [],
                "model": settings.OPENROUTER_MODEL,
                "history_turns_included": len(history) // 2,
            }

        # 4. Construct context string
        context_parts = []
        for i, src in enumerate(sources):
            context_parts.append(f"[Document: {src['source']} (Chunk {src['chunk_index']})]\n{src['content']}")
        context_text = "\n\n".join(context_parts)

        # 5. Generate LLM completion
        answer = self.generator.generate_answer(
            question=question,
            context_text=context_text,
            history=history,
        )

        # 6. Save turn to conversation memory
        self.memory.add_turn(session_id, question, answer)

        return {
            "answer": answer,
            "session_id": session_id,
            "question": question,
            "sources": sources,
            "model": settings.OPENROUTER_MODEL,
            "history_turns_included": len(history) // 2,
        }

    def answer_question_stream(
        self,
        question: str,
        session_id: str = "default",
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream RAG response tokens and yield metadata at conclusion."""
        k = top_k or settings.DEFAULT_TOP_K
        threshold = similarity_threshold if similarity_threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD

        history = self.memory.load_messages(session_id, limit=settings.MAX_HISTORY_TURNS * 2)

        sources = self.retriever.retrieve(
            query=question,
            top_k=k,
            similarity_threshold=threshold,
            db=db,
        )

        if not sources:
            fallback = "I do not have enough information in the provided documents to answer that question."
            yield {"type": "token", "content": fallback}
            self.memory.add_turn(session_id, question, fallback)
            yield {"type": "done", "sources": []}
            return

        context_parts = [
            f"[Document: {src['source']} (Chunk {src['chunk_index']})]\n{src['content']}"
            for src in sources
        ]
        context_text = "\n\n".join(context_parts)

        # Yield sources upfront or prepare for stream
        yield {"type": "sources", "sources": sources}

        full_answer = []
        token_stream = self.generator.generate_answer_stream(
            question=question,
            context_text=context_text,
            history=history,
        )

        for token in token_stream:
            full_answer.append(token)
            yield {"type": "token", "content": token}

        completed_answer = "".join(full_answer)
        self.memory.add_turn(session_id, question, completed_answer)
        yield {"type": "done"}


rag_service = RAGService()
