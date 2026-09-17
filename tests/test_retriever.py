import pytest
from app.services.ingestion import split_text_into_chunks, chunk_sentences
from app.services.retriever import retriever_service


def test_chunk_sentences():
    sentences = ["Sentence 1.", "Sentence 2.", "Sentence 3.", "Sentence 4."]
    chunks = chunk_sentences(sentences, chunk_size=2, overlap=1)
    assert len(chunks) == 3
    assert chunks[0] == "Sentence 1. Sentence 2."
    assert chunks[1] == "Sentence 2. Sentence 3."
    assert chunks[2] == "Sentence 3. Sentence 4."


def test_split_text_into_chunks():
    text = "First line here. Second line here! Third line follows? Final sentence."
    chunks = split_text_into_chunks(text, chunk_size=2, overlap=1)
    assert len(chunks) >= 2


def test_retriever_empty_query():
    results = retriever_service.retrieve("")
    assert results == []


def test_retriever_query():
    # Using existing company policy in DB
    results = retriever_service.retrieve("How many leave days do employees get?", top_k=2, similarity_threshold=0.2)
    assert isinstance(results, list)
    if len(results) > 0:
        assert "content" in results[0]
        assert "similarity" in results[0]
        assert results[0]["similarity"] >= 0.0
