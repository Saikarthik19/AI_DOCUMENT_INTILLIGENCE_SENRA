import os
import hashlib
import math
import re
from typing import List
from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class EmbeddingService:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL, target_dim: int = settings.EMBEDDING_DIM):
        self.model_name = model_name
        self.target_dim = target_dim
        self._model = None
        self._is_ready = False
        self._initialized_attempted = False

    def _ensure_model_loaded(self):
        if self._initialized_attempted:
            return

        self._initialized_attempted = True
        
        if self.model_name.lower().startswith("mock"):
            logger.info("Using deterministic offline embedding engine.")
            self._is_ready = True
            return

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info("Loading SentenceTransformer model '%s'...", self.model_name)
                self._model = SentenceTransformer(self.model_name)
                self._is_ready = True
                logger.info("SentenceTransformer model loaded successfully.")
                return
            except Exception as e:
                logger.warning("Could not download/load SentenceTransformer '%s': %s. Falling back to deterministic pseudo-embedding.", self.model_name, str(e))
        else:
            logger.warning("sentence-transformers not installed. Using deterministic fallback embeddings.")

    def is_ready(self) -> bool:
        return self._is_ready or self._initialized_attempted

    def _normalize(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return vec
        return [float(x / norm) for x in vec]

    def _deterministic_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized deterministic dense vector of target_dim length
        derived from character/word bag-of-words hashing with strictly positive weights.
        """
        vec = [0.0] * self.target_dim
        words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.target_dim
            vec[idx] += 1.0

        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self.target_dim
            vec[idx] += 1.5

        return self._normalize(vec)

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.target_dim

        self._ensure_model_loaded()

        if self._model is not None:
            try:
                emb = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return [float(x) for x in emb.tolist()]
            except Exception as e:
                logger.warning("SentenceTransformer inference error: %s. Using fallback.", str(e))

        return self._deterministic_embedding(text)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []

        self._ensure_model_loaded()

        if self._model is not None:
            try:
                embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    batch_embs = self._model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
                    embeddings.extend([list(map(float, e)) for e in batch_embs.tolist()])
                return embeddings
            except Exception as e:
                logger.warning("Batch encoding error: %s. Using fallback.", str(e))

        return [self._deterministic_embedding(t) for t in texts]

embedding_service = EmbeddingService()
