import pytest
from app.services.memory import memory_service


def test_memory_add_and_load():
    session_id = "test-session-1"
    memory_service.clear_messages(session_id)

    # Initially empty
    msgs = memory_service.load_messages(session_id)
    assert msgs == []

    # Add turn
    memory_service.add_turn(session_id, "Hello, assistant!", "Hello, human!")
    msgs = memory_service.load_messages(session_id)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello, assistant!"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == "Hello, human!"

    # Clean up
    memory_service.clear_messages(session_id)
    assert memory_service.load_messages(session_id) == []


def test_memory_turn_trimming():
    session_id = "test-session-trim"
    memory_service.clear_messages(session_id)

    # Add 12 turns with max_turns=5 (should keep only 10 messages)
    for i in range(12):
        memory_service.add_turn(session_id, f"User {i}", f"Assistant {i}", max_turns=5)

    msgs = memory_service.load_messages(session_id)
    assert len(msgs) == 10
    assert msgs[-1]["content"] == "Assistant 11"

    memory_service.clear_messages(session_id)
