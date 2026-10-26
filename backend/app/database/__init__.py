from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.base import BaseDatabase
from backend.app.database.mock_db import MockInMemoryDB
from backend.app.database.mongodb import MongoDBAtlas

_db_instance: Optional[BaseDatabase] = None

def get_database() -> BaseDatabase:
    global _db_instance
    if _db_instance is not None:
        return _db_instance

    if settings.MONGODB_URI and "mongodb" in settings.MONGODB_URI.lower():
        try:
            atlas_db = MongoDBAtlas(
                uri=settings.MONGODB_URI,
                db_name=settings.MONGODB_DATABASE,
                vector_index_name=settings.MONGODB_VECTOR_INDEX
            )
            if atlas_db.is_connected():
                logger.info("Using MongoDB Atlas database connection.")
                _db_instance = atlas_db
                return _db_instance
            else:
                logger.warning("MongoDB Atlas connection failed. Falling back to local in-memory storage.")
        except Exception as e:
            logger.error("Error initializing MongoDB Atlas: %s. Falling back to local in-memory storage.", str(e))

    logger.info("Operating in development mode using In-Memory Vector Storage.")
    _db_instance = MockInMemoryDB()
    return _db_instance

def reset_database_instance():
    global _db_instance
    _db_instance = None
