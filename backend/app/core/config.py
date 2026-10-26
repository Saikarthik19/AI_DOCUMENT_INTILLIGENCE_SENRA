import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # API & Server
    API_PREFIX: str = "/api"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ]
    
    # Upload limits
    MAX_UPLOAD_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"]
    
    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # MongoDB Atlas
    MONGODB_URI: Optional[str] = None
    MONGODB_DATABASE: str = "documind_db"
    MONGODB_DOCUMENTS_COLLECTION: str = "documents"
    MONGODB_CHUNKS_COLLECTION: str = "document_chunks"
    MONGODB_CONVERSATIONS_COLLECTION: str = "conversations"
    MONGODB_VECTOR_INDEX: str = "vector_index"
    
    # Vector Search & RAG
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.35
    
    # LLM Provider
    LLM_PROVIDER: str = "mock" # options: mock, openai, groq, gemini, ollama
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_TIMEOUT: int = 30
    
    # OCR
    OCR_ENABLED: bool = True
    TESSERACT_CMD: Optional[str] = None
    
    # Storage
    STORAGE_DIR: str = "data/uploads"

settings = Settings()
