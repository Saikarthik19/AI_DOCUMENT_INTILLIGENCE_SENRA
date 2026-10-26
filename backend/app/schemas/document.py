from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class DocumentChunkSchema(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    chunk_index: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size_bytes: int
    file_hash: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    status: str  # uploaded, processing, completed, failed
    total_pages: Optional[int] = None
    total_chunks: int = 0
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    status: str
    chunks_created: int = 0
    is_duplicate: bool = False

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]
