from pydantic import BaseModel, Field
from typing import List, Optional


class SourceChunk(BaseModel):
    source: str = Field(..., description="The document filename or source identifier")
    chunk_index: int = Field(..., description="Zero-based index of the chunk in the document")
    content: str = Field(..., description="Text content of the retrieved chunk")
    similarity: float = Field(..., description="Cosine similarity score between 0.0 and 1.0")
    distance: float = Field(..., description="Vector cosine distance")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000, description="User question or query", json_schema_extra={"example": "How many leave days do employees receive?"})
    session_id: str = Field(default="default", min_length=1, max_length=100, description="Session ID for conversational memory", json_schema_extra={"example": "user-123"})
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Number of document chunks to retrieve")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity score threshold")
    include_sources: bool = Field(default=True, description="Whether to include retrieved source chunks in response")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded LLM-generated answer")
    session_id: str = Field(..., description="Active session ID")
    question: str = Field(..., description="User question asked")
    sources: List[SourceChunk] = Field(default_factory=list, description="List of source chunks used as context")
    model: str = Field(..., description="LLM model used for generation")
    history_turns_included: int = Field(default=0, description="Number of prior conversation turns provided to the model")


class Message(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[Message]
    total_messages: int
