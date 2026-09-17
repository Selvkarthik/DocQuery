"""LLM answer generator adapter for backward compatibility."""

from app.core.config import settings
from app.services.generator import generator_service

MODEL = settings.OPENROUTER_MODEL


def _client():
    return generator_service._get_client()


def generate_answer(question: str, context: str):
    """Generate answer given context and question."""
    return generator_service.generate_answer(
        question=question,
        context_text=context,
    )
