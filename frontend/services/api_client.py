import os
import requests
from typing import Dict, Any, List, Optional

class APIClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("BACKEND_URL", "http://localhost:8000")).rstrip("/")
        self.timeout = 30

    def get_health(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=5)
            if res.status_code == 200:
                return res.json()
            return {"status": "unhealthy", "error": f"Status {res.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    def get_readiness(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/health/ready", timeout=5)
            if res.status_code == 200:
                return res.json()
            return {"status": "error", "error": f"Status {res.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/api/stats", timeout=5)
            if res.status_code == 200:
                return res.json()
            return {}
        except Exception:
            return {}

    def list_documents(self) -> List[Dict[str, Any]]:
        try:
            res = requests.get(f"{self.base_url}/api/documents", timeout=10)
            if res.status_code == 200:
                return res.json().get("documents", [])
            return []
        except Exception:
            return []

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = requests.get(f"{self.base_url}/api/documents/{document_id}", timeout=10)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        try:
            res = requests.get(f"{self.base_url}/api/documents/{document_id}/chunks", timeout=10)
            if res.status_code == 200:
                return res.json().get("chunks", [])
            return []
        except Exception:
            return []

    def upload_files(self, files_payload: List[tuple]) -> List[Dict[str, Any]]:
        # files_payload: list of ('files', (filename, file_bytes, mime_type))
        res = requests.post(f"{self.base_url}/api/documents/upload", files=files_payload, timeout=60)
        res.raise_for_status()
        return res.json()

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        res = requests.delete(f"{self.base_url}/api/documents/{document_id}", timeout=10)
        res.raise_for_status()
        return res.json()

    def reprocess_document(self, document_id: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api/documents/{document_id}/reprocess", timeout=30)
        res.raise_for_status()
        return res.json()

    def ask_chat(self, question: str, document_id: Optional[str] = None, top_k: Optional[int] = None, similarity_threshold: Optional[float] = None) -> Dict[str, Any]:
        payload = {
            "question": question,
            "document_id": document_id,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }
        res = requests.post(f"{self.base_url}/api/chat/ask", json=payload, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

api_client = APIClient()
