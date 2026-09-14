import redis
import json

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

def load_messages(session_id):
    data = redis_client.get(f"session: {session_id}")

    if data:
        return json.loads(data)
    return []

def save_messages(session_id, messages):
    redis_client.set(f"session: {session_id}", json.dumps(messages))