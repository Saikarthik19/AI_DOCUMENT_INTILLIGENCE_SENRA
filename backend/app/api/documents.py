import hashlib
import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import DocumentProcessingError, DocumentNotFoundError
from backend.app.database import get_database
from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentListResponse
from backend.app.services.document_parser import document_parser
from backend.app.services.text_chunker import text_chunker
from backend.app.services.embedding_service import embedding_service

router = APIRouter(prefix="/api/documents", tags=["Documents"])

def sanitize_filename(filename: str) -> str:
    # Strip any directory components
    base = os.path.basename(filename)
    # Remove null bytes and strange control characters
    clean = "".join(c for c in base if c.isalnum() or c in "._- ")
    return clean or "unnamed_document"

def process_document_pipeline(document_id: str, filename: str, content: bytes, file_type: str):
    db = get_database()
    try:
        db.update_document_status(document_id, "processing")
        
        # 1. Parse document
        parsed_doc = document_parser.parse(filename, content, file_type=file_type)
        
        # 2. Chunk document
        chunks = text_chunker.chunk_document(document_id, parsed_doc)
        
        if not chunks:
            db.update_document_status(
                document_id,
                status="completed",
                total_pages=parsed_doc.total_pages,
                total_chunks=0,
                error_message="Document parsed successfully but no textual content was found."
            )
            return

        # 3. Generate embeddings
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        
        for c, emb in zip(chunks, embeddings):
            c["embedding"] = emb

        # 4. Remove any prior chunks if retrying / reprocessing
        db.delete_chunks_by_document(document_id)

        # 5. Insert new chunks
        db.insert_chunks(chunks)

        # 6. Mark document as completed
        db.update_document_status(
            document_id,
            status="completed",
            total_pages=parsed_doc.total_pages,
            total_chunks=len(chunks)
        )
        logger.info("Successfully ingested document '%s' (ID: %s) with %d chunks.", filename, document_id, len(chunks))

    except Exception as e:
        logger.error("Error processing document '%s': %s", filename, str(e))
        db.update_document_status(
            document_id,
            status="failed",
            error_message=str(e)
        )

@router.post("/upload", response_model=List[DocumentUploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    db = get_database()
    responses: List[DocumentUploadResponse] = []
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024

    for file in files:
        filename = sanitize_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' is empty (0 bytes)."
            )

        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{filename}' exceeds maximum allowed upload size of {settings.MAX_UPLOAD_MB}MB."
            )

        # Calculate file hash for duplicate detection
        file_hash = hashlib.sha256(content).hexdigest()
        existing_doc = db.get_document_by_hash(file_hash)

        if existing_doc:
            logger.info("Duplicate document detected for '%s' (Hash: %s).", filename, file_hash)
            responses.append(DocumentUploadResponse(
                message="Duplicate file detected. Existing document record returned.",
                document_id=existing_doc["document_id"],
                filename=existing_doc["filename"],
                status=existing_doc["status"],
                chunks_created=existing_doc.get("total_chunks", 0),
                is_duplicate=True
            ))
            continue

        document_id = f"doc_{uuid.uuid4().hex[:10]}"
        file_type = ext.replace(".", "")
        now = datetime.now(timezone.utc)

        doc_record = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "file_size_bytes": file_size,
            "file_hash": file_hash,
            "status": "processing",
            "total_pages": None,
            "total_chunks": 0,
            "created_at": now,
            "updated_at": now,
            "error_message": None,
            "metadata": {}
        }
        db.insert_document(doc_record)

        # Process document
        process_document_pipeline(document_id, filename, content, file_type)
        
        # Reload to get final state
        updated_doc = db.get_document(document_id)
        final_status = updated_doc.get("status", "completed") if updated_doc else "completed"
        chunks_count = updated_doc.get("total_chunks", 0) if updated_doc else 0

        responses.append(DocumentUploadResponse(
            message="Document uploaded and processed successfully." if final_status == "completed" else "Document uploaded, processing failed.",
            document_id=document_id,
            filename=filename,
            status=final_status,
            chunks_created=chunks_count,
            is_duplicate=False
        ))

    return responses

@router.get("", response_model=DocumentListResponse)
def list_documents(skip: int = 0, limit: int = 50):
    db = get_database()
    docs = db.list_documents(skip=skip, limit=limit)
    total = db.count_documents()
    return DocumentListResponse(total=total, documents=docs)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str):
    db = get_database()
    doc = db.get_document(document_id)
    if not doc:
        raise DocumentNotFoundError(document_id)
    return doc

@router.delete("/{document_id}")
def delete_document(document_id: str):
    db = get_database()
    doc = db.get_document(document_id)
    if not doc:
        raise DocumentNotFoundError(document_id)

    success = db.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document from database.")

    return {
        "message": f"Document '{document_id}' and all its associated chunks were successfully deleted.",
        "document_id": document_id
    }

@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(document_id: str):
    db = get_database()
    doc = db.get_document(document_id)
    if not doc:
        raise DocumentNotFoundError(document_id)

    # In our architecture, if the chunks already exist, we re-verify them
    chunks = db.get_chunks_by_document(document_id)
    if chunks:
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        for c, emb in zip(chunks, embeddings):
            c["embedding"] = emb
        db.delete_chunks_by_document(document_id)
        db.insert_chunks(chunks)
        db.update_document_status(document_id, "completed", total_chunks=len(chunks), error_message=None)
    else:
        db.update_document_status(document_id, "completed", total_chunks=0, error_message=None)

    updated_doc = db.get_document(document_id)
    return updated_doc

@router.get("/{document_id}/chunks")
def get_document_chunks(document_id: str):
    db = get_database()
    doc = db.get_document(document_id)
    if not doc:
        raise DocumentNotFoundError(document_id)
    chunks = db.get_chunks_by_document(document_id)
    # Exclude raw high-dimensional embeddings for clean response
    for c in chunks:
        c.pop("embedding", None)
    return {"document_id": document_id, "total_chunks": len(chunks), "chunks": chunks}
