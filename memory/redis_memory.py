"""Redis memory adapter for backward compatibility."""

from app.services.memory import memory_service

redis_client = memory_service.client


def load_messages(session_id: str):
    """Load conversation messages for a session."""
    return memory_service.load_messages(session_id)


def save_messages(session_id: str, messages):
    """Save conversation messages for a session."""
    return memory_service.save_messages(session_id, messages)