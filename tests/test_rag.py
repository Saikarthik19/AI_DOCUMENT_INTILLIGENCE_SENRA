import pytest
from backend.app.database.mock_db import MockInMemoryDB
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_search_service import VectorSearchService
from backend.app.services.embedding_service import embedding_service

@pytest.fixture
def populated_mock_db(monkeypatch):
    db = MockInMemoryDB()
    # Insert document
    db.insert_document({
        "document_id": "doc_inv_1001",
        "filename": "Invoice_1001.pdf",
        "file_type": "pdf",
        "file_size_bytes": 1024,
        "file_hash": "hash123",
        "status": "completed",
        "total_pages": 1,
        "total_chunks": 1
    })

    # Insert chunk with embedding
    text = "The total amount in Invoice_1001.pdf is $12,450.00 for Acme Consulting Services."
    emb = embedding_service.embed_text(text)
    db.insert_chunks([{
        "chunk_id": "chunk_1001",
        "document_id": "doc_inv_1001",
        "filename": "Invoice_1001.pdf",
        "page_number": 1,
        "chunk_index": 0,
        "text": text,
        "embedding": emb,
        "metadata": {}
    }])

    # Monkeypatch get_database
    monkeypatch.setattr("backend.app.database.get_database", lambda: db)
    monkeypatch.setattr("backend.app.services.vector_search_service.get_database", lambda: db)
    return db

def test_rag_answer_with_citations(populated_mock_db):
    rag = RAGService()
    # Force mock provider for deterministic unit test
    rag.provider = "mock"

    res = rag.answer_query("What is the total amount in Invoice_1001.pdf?")
    assert res.has_sufficient_context is True
    assert "$12,450.00" in res.answer or "Invoice_1001.pdf" in res.answer
    assert len(res.citations) > 0
    assert res.citations[0].filename == "Invoice_1001.pdf"
    assert res.citations[0].page_number == 1

def test_rag_no_evidence(populated_mock_db):
    rag = RAGService()
    rag.provider = "mock"

    # Search for something completely unrelated with high threshold
    res = rag.answer_query(
        "What is the airspeed velocity of an unladen swallow?",
        similarity_threshold=0.99
    )
    assert res.has_sufficient_context is False
    assert "do not contain sufficient" in res.answer.lower()
    assert len(res.citations) == 0
