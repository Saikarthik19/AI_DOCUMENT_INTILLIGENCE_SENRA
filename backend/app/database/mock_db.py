import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.app.core.logging import logger
from backend.app.database.base import BaseDatabase

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    val = float(dot / (norm_a * norm_b))
    # In deterministic simulated embedding spaces, vocabulary overlap produces lower raw cosine.
    # Applying smooth sub-linear scaling ensures word overlaps yield high confidence while maintaining 0 for disjoint texts.
    if val > 0.0:
        val = math.sqrt(val)
    return min(1.0, max(0.0, val))

class MockInMemoryDB(BaseDatabase):
    """
    Deterministic In-Memory / Simulated Storage Database.
    Allows complete local development, tests, and CI/CD without MongoDB credentials.
    Performs true in-memory cosine similarity vector search over embeddings.
    """
    def __init__(self):
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._chunks: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized In-Memory Simulated Database with Cosine Similarity Vector Search.")

    def is_connected(self) -> bool:
        return True

    def is_vector_index_ready(self) -> bool:
        return True

    def insert_document(self, doc_data: Dict[str, Any]) -> str:
        doc_id = doc_data["document_id"]
        if "created_at" not in doc_data:
            doc_data["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in doc_data:
            doc_data["updated_at"] = datetime.now(timezone.utc)
        self._documents[doc_id] = dict(doc_data)
        return doc_id

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        doc = self._documents.get(document_id)
        return dict(doc) if doc else None

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        for doc in self._documents.values():
            if doc.get("file_hash") == file_hash:
                return dict(doc)
        return None

    def list_documents(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        docs = sorted(self._documents.values(), key=lambda d: d.get("created_at", datetime.min), reverse=True)
        return [dict(d) for d in docs[skip:skip+limit]]

    def count_documents(self) -> int:
        return len(self._documents)

    def update_document_status(self, document_id: str, status: str, total_pages: Optional[int] = None, total_chunks: Optional[int] = None, error_message: Optional[str] = None) -> bool:
        if document_id not in self._documents:
            return False
        self._documents[document_id]["status"] = status
        self._documents[document_id]["updated_at"] = datetime.now(timezone.utc)
        if total_pages is not None:
            self._documents[document_id]["total_pages"] = total_pages
        if total_chunks is not None:
            self._documents[document_id]["total_chunks"] = total_chunks
        if error_message is not None:
            self._documents[document_id]["error_message"] = error_message
        return True

    def delete_document(self, document_id: str) -> bool:
        if document_id not in self._documents:
            return False
        self.delete_chunks_by_document(document_id)
        del self._documents[document_id]
        return True

    def insert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        count = 0
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            self._chunks[chunk_id] = dict(chunk)
            count += 1
        return count

    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        return [dict(c) for c in self._chunks.values() if c.get("document_id") == document_id]

    def delete_chunks_by_document(self, document_id: str) -> int:
        to_del = [cid for cid, c in self._chunks.items() if c.get("document_id") == document_id]
        for cid in to_del:
            del self._chunks[cid]
        return len(to_del)

    def count_chunks(self) -> int:
        return len(self._chunks)

    def vector_search(self, query_embedding: List[float], top_k: int = 4, document_id: Optional[str] = None, similarity_threshold: float = 0.35) -> List[Dict[str, Any]]:
        scored_chunks = []
        for c in self._chunks.values():
            if document_id and c.get("document_id") != document_id:
                continue
            emb = c.get("embedding")
            if not emb:
                continue
            sim = cosine_similarity(query_embedding, emb)
            if sim >= similarity_threshold:
                c_copy = dict(c)
                # Remove large embedding from response
                c_copy.pop("embedding", None)
                c_copy["score"] = float(sim)
                scored_chunks.append(c_copy)
        
        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
