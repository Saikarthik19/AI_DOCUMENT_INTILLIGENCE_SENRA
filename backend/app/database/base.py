from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseDatabase(ABC):
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def is_vector_index_ready(self) -> bool:
        pass

    @abstractmethod
    def insert_document(self, doc_data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list_documents(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def count_documents(self) -> int:
        pass

    @abstractmethod
    def update_document_status(self, document_id: str, status: str, total_pages: Optional[int] = None, total_chunks: Optional[int] = None, error_message: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        pass

    @abstractmethod
    def insert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_chunks_by_document(self, document_id: str) -> int:
        pass

    @abstractmethod
    def count_chunks(self) -> int:
        pass

    @abstractmethod
    def vector_search(self, query_embedding: List[float], top_k: int = 4, document_id: Optional[str] = None, similarity_threshold: float = 0.35) -> List[Dict[str, Any]]:
        pass
