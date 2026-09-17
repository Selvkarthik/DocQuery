import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.rag_service import rag_service
from app.services.memory import memory_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceChunk,
    SessionHistoryResponse,
    Message,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question with conversational memory",
    description="Performs semantic vector retrieval over indexed documents and generates an answer using OpenRouter LLM, retaining multi-turn context in Redis.",
)
def chat_with_documents(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = rag_service.answer_question(
            question=request.question,
            session_id=request.session_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            db=db,
        )

        sources = []
        if request.include_sources:
            for s in result.get("sources", []):
                sources.append(
                    SourceChunk(
                        source=s["source"],
                        chunk_index=s["chunk_index"],
                        content=s["content"],
                        similarity=s["similarity"],
                        distance=s["distance"],
                    )
                )

        return ChatResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            question=result["question"],
            sources=sources,
            model=result["model"],
            history_turns_included=result.get("history_turns_included", 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing chat: {str(e)}",
        )


@router.post(
    "/stream",
    summary="Stream question answer via Server-Sent Events (SSE)",
    description="Streams generated response tokens in real-time.",
)
def stream_chat_with_documents(request: ChatRequest, db: Session = Depends(get_db)):
    def event_stream():
        try:
            generator = rag_service.answer_question_stream(
                question=request.question,
                session_id=request.session_id,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold,
                db=db,
            )
            for item in generator:
                yield f"data: {json.dumps(item)}\n\n"
        except Exception as e:
            error_payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get(
    "/history/{session_id}",
    response_model=SessionHistoryResponse,
    summary="Retrieve session chat history",
    description="Fetches recent message turns stored in Redis for the given session ID.",
)
def get_session_history(session_id: str):
    raw_messages = memory_service.load_messages(session_id)
    messages = [
        Message(
            role=m.get("role", "user"),
            content=m.get("content", ""),
            timestamp=m.get("timestamp"),
        )
        for m in raw_messages
    ]
    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        total_messages=len(messages),
    )


@router.delete(
    "/history/{session_id}",
    summary="Clear session memory",
    description="Deletes all conversation messages for the given session ID from Redis.",
)
def clear_session_history(session_id: str):
    cleared = memory_service.clear_messages(session_id)
    return {
        "session_id": session_id,
        "cleared": cleared,
        "message": f"Session history for '{session_id}' has been cleared.",
    }
