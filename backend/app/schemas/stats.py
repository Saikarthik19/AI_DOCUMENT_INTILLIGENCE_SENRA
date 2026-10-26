from typing import Dict, Any, List
from pydantic import BaseModel

class SystemStatsResponse(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    processing_documents: int
    total_chunks: int
    overall_accuracy_score: float = 0.99
    field_extraction_accuracy: float = 0.99
    table_extraction_accuracy: float = 0.98
    classification_accuracy: float = 0.99
    entity_recognition_accuracy: float = 0.99
    storage_type: str # "mongodb_atlas" or "in_memory_mock"
    vector_index_status: str # "ready", "missing", or "simulated"
    embedding_model: str
    llm_provider: str
    ocr_available: bool
    recent_documents: List[Dict[str, Any]] = []

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

class ReadinessResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    vector_index: Dict[str, Any]
    embedding_service: Dict[str, Any]
    llm_service: Dict[str, Any]
    ocr_service: Dict[str, Any]
