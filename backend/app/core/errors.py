from fastapi import HTTPException, status

class DocumentProcessingError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class DatabaseConnectionError(HTTPException):
    def __init__(self, detail: str = "Database connection unavailable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

class VectorSearchError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class DocumentNotFoundError(HTTPException):
    def __init__(self, document_id: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found")
