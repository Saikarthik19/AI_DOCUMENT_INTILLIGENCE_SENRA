import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.document_parser import ParsedDocument

class TextChunker:
    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        # chunk_size in characters (approx 4 chars per token -> 800 tokens is approx 3200 chars or configurable)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document_id: str, parsed_doc: ParsedDocument) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0
        now_ts = datetime.now(timezone.utc)

        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_chunks = self._split_text(page_text)
            for text_piece in page_chunks:
                chunk_id = f"{document_id}_chk_{global_chunk_idx}_{uuid.uuid4().hex[:6]}"
                chunk_record = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "filename": parsed_doc.filename,
                    "page_number": page.page_number,
                    "chunk_index": global_chunk_idx,
                    "text": text_piece,
                    "metadata": {
                        **page.metadata,
                        "created_at": now_ts.isoformat(),
                        "char_length": len(text_piece),
                        "file_type": parsed_doc.file_type
                    }
                }
                chunks.append(chunk_record)
                global_chunk_idx += 1

        logger.info("Chunked document '%s' (ID: %s) into %d chunks.", parsed_doc.filename, document_id, len(chunks))
        return chunks

    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        # First split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        result_chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If a single paragraph exceeds chunk size, split it into sentences
            if len(para) > self.chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            result_chunks.append(current_chunk)
                            overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                            current_chunk = current_chunk[overlap_start:].strip()
                            if current_chunk:
                                current_chunk = f"{current_chunk} {sentence}".strip()
                            else:
                                current_chunk = sentence
                        else:
                            # Hard split if single sentence is exceptionally long
                            while len(sentence) > self.chunk_size:
                                result_chunks.append(sentence[:self.chunk_size])
                                sentence = sentence[self.chunk_size - self.chunk_overlap:]
                            current_chunk = sentence
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk = f"{current_chunk}\n\n{para}".strip()
                else:
                    if current_chunk:
                        result_chunks.append(current_chunk)
                        overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                        current_chunk = current_chunk[overlap_start:].strip()
                        if current_chunk:
                            current_chunk = f"{current_chunk}\n\n{para}".strip()
                        else:
                            current_chunk = para
                    else:
                        current_chunk = para

        if current_chunk:
            result_chunks.append(current_chunk)

        return result_chunks

text_chunker = TextChunker()
