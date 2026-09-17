import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


def test_system_info_endpoint():
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "DocQuery"
    assert data["embedding_dimension"] == 384
    assert "total_chunks" in data


def test_search_endpoint():
    response = client.post(
        "/api/v1/search",
        json={"query": "leave policy", "top_k": 2, "similarity_threshold": 0.1}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_results" in data


def test_documents_list_endpoint():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total_documents" in data


def test_legacy_ask_endpoint():
    response = client.post(
        "/ask",
        json={"session_id": "test-legacy", "question": "leave days for employees"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


def test_v1_chat_and_history_lifecycle():
    session_id = "test-lifecycle-session"
    # Ensure starting clean
    client.delete(f"/api/v1/chat/history/{session_id}")

    # 1. Ask question
    res = client.post(
        "/api/v1/chat",
        json={
            "question": "How many days leave do interns receive?",
            "session_id": session_id,
            "top_k": 2,
            "similarity_threshold": 0.2,
            "include_sources": True
        }
    )
    assert res.status_code == 200
    chat_data = res.json()
    assert "answer" in chat_data
    assert len(chat_data["sources"]) > 0

    # 2. Check history recorded in Redis
    hist_res = client.get(f"/api/v1/chat/history/{session_id}")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total_messages"] >= 2
    assert hist_data["messages"][0]["role"] == "user"
    assert hist_data["messages"][1]["role"] == "assistant"

    # 3. Clear session
    del_res = client.delete(f"/api/v1/chat/history/{session_id}")
    assert del_res.status_code == 200

    # 4. Verify cleared
    empty_hist = client.get(f"/api/v1/chat/history/{session_id}").json()
    assert empty_hist["total_messages"] == 0
