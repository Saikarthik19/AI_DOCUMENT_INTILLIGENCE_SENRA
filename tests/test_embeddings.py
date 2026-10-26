import pytest
from backend.app.services.embedding_service import EmbeddingService

def test_embedding_dimensions():
    service = EmbeddingService(target_dim=384)
    emb = service.embed_text("DocuMind AI vector search evaluation")
    assert isinstance(emb, list)
    assert len(emb) == 384
    # Check normalization: sum of squares is approximately 1.0
    norm_sq = sum(x * x for x in emb)
    assert pytest.approx(norm_sq, 0.05) == 1.0

def test_batch_embedding():
    service = EmbeddingService(target_dim=384)
    texts = ["Invoice 1001 payment details", "Contract agreement terms and SLA"]
    embs = service.embed_batch(texts)
    assert len(embs) == 2
    assert len(embs[0]) == 384
    assert len(embs[1]) == 384
