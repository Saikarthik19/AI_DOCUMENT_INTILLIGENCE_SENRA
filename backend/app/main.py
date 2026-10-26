from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database import get_database
from backend.app.api.health import router as health_router
from backend.app.api.documents import router as documents_router
from backend.app.api.chat import router as chat_router
from backend.app.api.stats import router as stats_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    db = get_database()
    logger.info("Database initialized: %s", db.__class__.__name__)
    yield
    logger.info("DocuMind AI application shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DocuMind AI — Intelligent Document Analysis, OCR, and RAG Platform",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc), "path": request.url.path}
    )

# Routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(stats_router)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
