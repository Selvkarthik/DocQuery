import json
import time
from typing import List, Dict, Any, Optional
import redis
from app.core.config import settings
from app.core.logging import logger


class RedisMemoryService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._fallback_memory: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
        return self._client

    def _format_key(self, session_id: str) -> str:
        clean_id = session_id.strip() or "default"
        return f"docquery:session:{clean_id}"

    def is_healthy(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    def load_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load chat history for a session from Redis (or fallback in-memory cache)."""
        key = self._format_key(session_id)
        try:
            raw_data = self.client.get(key)
            if raw_data:
                messages = json.loads(raw_data)
                if limit and len(messages) > limit:
                    return messages[-limit:]
                return messages
            return []
        except Exception as e:
            logger.warning(f"Error reading from Redis for session '{session_id}': {e}. Using local cache.")
            messages = self._fallback_memory.get(key, [])
            if limit and len(messages) > limit:
                return messages[-limit:]
            return messages

    def save_messages(self, session_id: str, messages: List[Dict[str, Any]], ttl_seconds: Optional[int] = None) -> bool:
        """Save chat messages for a session with optional TTL."""
        key = self._format_key(session_id)
        ttl = ttl_seconds or settings.REDIS_TTL_SECONDS
        try:
            payload = json.dumps(messages)
            self.client.set(key, payload, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Error saving to Redis for session '{session_id}': {e}. Storing in local cache.")
            self._fallback_memory[key] = messages
            return False

    def add_turn(self, session_id: str, user_content: str, assistant_content: str, max_turns: int = 10) -> None:
        """Append a user/assistant turn and retain only the recent max_turns."""
        history = self.load_messages(session_id)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        history.append({"role": "user", "content": user_content, "timestamp": timestamp})
        history.append({"role": "assistant", "content": assistant_content, "timestamp": timestamp})

        max_messages = max_turns * 2
        trimmed = history[-max_messages:]
        self.save_messages(session_id, trimmed)

    def clear_messages(self, session_id: str) -> bool:
        """Clear conversation memory for a session."""
        key = self._format_key(session_id)
        cleared = False
        try:
            cleared = bool(self.client.delete(key))
        except Exception as e:
            logger.warning(f"Error deleting Redis session '{session_id}': {e}")
        if key in self._fallback_memory:
            del self._fallback_memory[key]
            cleared = True
        return cleared


memory_service = RedisMemoryService()
