from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.database import get_database
from backend.app.services.embedding_service import embedding_service
from backend.app.services.ocr_service import ocr_service
from backend.app.schemas.stats import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )

@router.get("/health/ready", response_model=ReadinessResponse)
def readiness_check():
    db = get_database()
    db_connected = db.is_connected()
    vector_ready = db.is_vector_index_ready()

    is_overall_ready = db_connected

    return ReadinessResponse(
        status="ready" if is_overall_ready else "degraded",
        database={
            "connected": db_connected,
            "type": "mongodb_atlas" if "MongoDBAtlas" in db.__class__.__name__ else "in_memory_mock"
        },
        vector_index={
            "ready": vector_ready,
            "index_name": settings.MONGODB_VECTOR_INDEX
        },
        embedding_service={
            "model": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIM,
            "sentence_transformers_loaded": embedding_service.is_ready()
        },
        llm_service={
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "configured": bool(settings.LLM_API_KEY) if settings.LLM_PROVIDER not in ["mock", "ollama"] else True
        },
        ocr_service={
            "enabled": settings.OCR_ENABLED,
            "available": ocr_service.is_available()
        }
    )
