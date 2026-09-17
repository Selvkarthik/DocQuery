"""Agent tools for backward compatibility."""

from app.services.retriever import retriever_service
from app.services.agent_service import tool_calculate_percentage


def search_company_document(question: str):
    """Search documents and return list of matches."""
    return retriever_service.retrieve(question, top_k=2)


def calculate_percentage(part: float, whole: float):
    """Calculate percentage."""
    return tool_calculate_percentage(part, whole)
