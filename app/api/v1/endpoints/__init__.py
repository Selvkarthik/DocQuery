from .health import router as health_router
from .chat import router as chat_router
from .documents import router as documents_router
from .search import router as search_router
from .agent import router as agent_router

__all__ = [
    "health_router",
    "chat_router",
    "documents_router",
    "search_router",
    "agent_router",
]
