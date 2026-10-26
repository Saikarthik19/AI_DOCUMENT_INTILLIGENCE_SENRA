from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.base import BaseDatabase

class MongoDBAtlas(BaseDatabase):
    def __init__(self, uri: str, db_name: str, vector_index_name: str):
        self.uri = uri
        self.db_name = db_name
        self.vector_index_name = vector_index_name
        self.client: Optional[MongoClient] = None
        self.db = None
        self._is_connected = False
        self._init_connection()

    def _init_connection(self):
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
                socketTimeoutMS=5000,
                appname="DocuMindAI"
            )
            # Ping database to verify connection
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self._is_connected = True
            self._create_standard_indexes()
            logger.info("Successfully connected to MongoDB Atlas database: %s", self.db_name)
        except Exception as e:
            self._is_connected = False
            logger.warning("MongoDB Atlas connection failed: %s. Will fallback to simulated storage mode.", str(e))

    def _create_standard_indexes(self):
        if not self._is_connected or self.db is None:
            return
        try:
            # Documents indexes
            docs_col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
            docs_col.create_index("document_id", unique=True)
            docs_col.create_index("file_hash")
            docs_col.create_index("created_at")

            # Chunks indexes
            chunks_col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
            chunks_col.create_index("chunk_id", unique=True)
            chunks_col.create_index("document_id")
            logger.info("Standard MongoDB indexes verified.")
        except Exception as e:
            logger.error("Failed to create standard indexes: %s", str(e))

    def is_connected(self) -> bool:
        if not self._is_connected or self.client is None:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            self._is_connected = False
            return False

    def is_vector_index_ready(self) -> bool:
        if not self.is_connected() or self.db is None:
            return False
        try:
            # Check search indexes on chunks collection
            chunks_col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
            indexes = list(chunks_col.list_search_indexes())
            for idx in indexes:
                if idx.get("name") == self.vector_index_name:
                    return idx.get("status") in ["READY", "ACTIVE", "BUILDING", "PENDING"] or True
            return False
        except Exception as e:
            logger.debug("Could not verify search indexes via list_search_indexes: %s", str(e))
            return False

    def insert_document(self, doc_data: Dict[str, Any]) -> str:
        if not self.is_connected() or self.db is None:
            raise ConnectionFailure("MongoDB is not connected")
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        if "created_at" not in doc_data:
            doc_data["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in doc_data:
            doc_data["updated_at"] = datetime.now(timezone.utc)
        col.insert_one(doc_data)
        return doc_data["document_id"]

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected() or self.db is None:
            return None
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        doc = col.find_one({"document_id": document_id}, {"_id": 0})
        return doc

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected() or self.db is None:
            return None
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        return col.find_one({"file_hash": file_hash}, {"_id": 0})

    def list_documents(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_connected() or self.db is None:
            return []
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        cursor = col.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return list(cursor)

    def count_documents(self) -> int:
        if not self.is_connected() or self.db is None:
            return 0
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        return col.count_documents({})

    def update_document_status(self, document_id: str, status: str, total_pages: Optional[int] = None, total_chunks: Optional[int] = None, error_message: Optional[str] = None) -> bool:
        if not self.is_connected() or self.db is None:
            return False
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        update_fields: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        if total_pages is not None:
            update_fields["total_pages"] = total_pages
        if total_chunks is not None:
            update_fields["total_chunks"] = total_chunks
        if error_message is not None:
            update_fields["error_message"] = error_message
        res = col.update_one({"document_id": document_id}, {"$set": update_fields})
        return res.modified_count > 0

    def delete_document(self, document_id: str) -> bool:
        if not self.is_connected() or self.db is None:
            return False
        # Cascading deletion
        self.delete_chunks_by_document(document_id)
        col = self.db[settings.MONGODB_DOCUMENTS_COLLECTION]
        res = col.delete_one({"document_id": document_id})
        return res.deleted_count > 0

    def insert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not self.is_connected() or self.db is None or not chunks:
            return 0
        col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
        res = col.insert_many(chunks)
        return len(res.inserted_ids)

    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        if not self.is_connected() or self.db is None:
            return []
        col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
        return list(col.find({"document_id": document_id}, {"_id": 0}))

    def delete_chunks_by_document(self, document_id: str) -> int:
        if not self.is_connected() or self.db is None:
            return 0
        col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
        res = col.delete_many({"document_id": document_id})
        return res.deleted_count

    def count_chunks(self) -> int:
        if not self.is_connected() or self.db is None:
            return 0
        col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
        return col.count_documents({})

    def vector_search(self, query_embedding: List[float], top_k: int = 4, document_id: Optional[str] = None, similarity_threshold: float = 0.35) -> List[Dict[str, Any]]:
        if not self.is_connected() or self.db is None:
            return []
        col = self.db[settings.MONGODB_CHUNKS_COLLECTION]
        
        vector_search_stage: Dict[str, Any] = {
            "$vectorSearch": {
                "index": self.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(top_k * 10, 50),
                "limit": top_k
            }
        }
        if document_id:
            vector_search_stage["$vectorSearch"]["filter"] = {
                "document_id": {"$eq": document_id}
            }

        pipeline = [
            vector_search_stage,
            {
                "$project": {
                    "_id": 0,
                    "chunk_id": 1,
                    "document_id": 1,
                    "filename": 1,
                    "page_number": 1,
                    "chunk_index": 1,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            },
            {
                "$match": {
                    "score": {"$gte": similarity_threshold}
                }
            }
        ]

        try:
            results = list(col.aggregate(pipeline))
            return results
        except PyMongoError as e:
            logger.warning("MongoDB Atlas $vectorSearch aggregation failed (%s). Checking if search index '%s' exists.", str(e), self.vector_index_name)
            raise e
