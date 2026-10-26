from typing import List, Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database import get_database
from backend.app.services.embedding_service import embedding_service

class VectorSearchService:
    def __init__(self):
        pass

    @property
    def db(self):
        return get_database()

    def search(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.TOP_K
        threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD

        logger.info("Executing vector search for query: '%s' (top_k=%d, threshold=%.2f, filter_doc=%s)",
                    query[:50], k, threshold, document_id)

        # 1. Generate query embedding
        query_vector = embedding_service.embed_text(query)

        # 2. Query database
        try:
            results = self.db.vector_search(
                query_embedding=query_vector,
                top_k=k,
                document_id=document_id,
                similarity_threshold=threshold
            )
            logger.info("Vector search returned %d matching chunks above threshold %.2f", len(results), threshold)
            return results
        except Exception as e:
            logger.error("Vector search failed in database: %s", str(e))
            raise e

vector_search_service = VectorSearchService()
