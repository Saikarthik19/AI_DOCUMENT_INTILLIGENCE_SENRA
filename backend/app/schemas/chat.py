from typing import List, Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: Optional[int] = None
    chunk_id: str
    excerpt: str
    similarity_score: Optional[float] = None

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000, description="The user query to search and answer")
    document_id: Optional[str] = Field(default=None, description="Optional document ID to restrict search context")
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    stream: bool = False

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    has_sufficient_context: bool = True
    model_used: str
    query: str
