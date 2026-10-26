import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import get_database

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_readiness_endpoint(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert "database" in data
    assert "embedding_service" in data

def test_upload_and_delete_document_lifecycle(client):
    # 1. Upload sample text document
    file_content = b"ACME Corp Contract Agreement. Terms: 30 days net payment. Total: $50,000."
    res = client.post(
        "/api/documents/upload",
        files=[("files", ("contract.txt", file_content, "text/plain"))]
    )
    assert res.status_code == 200
    upload_data = res.json()
    assert len(upload_data) == 1
    doc_id = upload_data[0]["document_id"]
    assert upload_data[0]["filename"] == "contract.txt"

    # 2. Get document details
    res_get = client.get(f"/api/documents/{doc_id}")
    assert res_get.status_code == 200
    assert res_get.json()["document_id"] == doc_id

    # 3. Ask question via chat
    res_chat = client.post(
        "/api/chat/ask",
        json={"question": "What are the payment terms?", "document_id": doc_id}
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert chat_data["has_sufficient_context"] is True
    assert len(chat_data["citations"]) > 0

    # 4. Delete document
    res_del = client.delete(f"/api/documents/{doc_id}")
    assert res_del.status_code == 200

    # 5. Verify document deleted
    res_get_del = client.get(f"/api/documents/{doc_id}")
    assert res_get_del.status_code == 404

    # 6. Verify chunks cascaded
    db = get_database()
    chunks = db.get_chunks_by_document(doc_id)
    assert len(chunks) == 0

def test_upload_duplicate_detection(client):
    file_content = b"Duplicate detection content unique test string 998877."
    # First upload
    res1 = client.post(
        "/api/documents/upload",
        files=[("files", ("dup_test.txt", file_content, "text/plain"))]
    )
    assert res1.status_code == 200
    d1 = res1.json()[0]
    assert d1["is_duplicate"] is False

    # Second upload with exact same hash
    res2 = client.post(
        "/api/documents/upload",
        files=[("files", ("dup_test.txt", file_content, "text/plain"))]
    )
    assert res2.status_code == 200
    d2 = res2.json()[0]
    assert d2["is_duplicate"] is True
    assert d2["document_id"] == d1["document_id"]

    # Cleanup
    client.delete(f"/api/documents/{d1['document_id']}")
