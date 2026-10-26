from fastapi import APIRouter, HTTPException, status
from backend.app.core.logging import logger
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/ask", response_model=ChatResponse)
def ask_question(request: ChatRequest):
    try:
        response = rag_service.answer_query(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        return response
    except Exception as e:
        logger.error("Chat question execution error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing RAG pipeline: {str(e)}"
        )
