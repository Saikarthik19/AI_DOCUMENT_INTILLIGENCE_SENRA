import pytest
from backend.app.services.text_chunker import TextChunker
from backend.app.services.document_parser import ParsedDocument, ParsedPage

def test_text_chunking_and_overlap():
    chunker = TextChunker(chunk_size=150, chunk_overlap=30)
    text = (
        "Artificial Intelligence is transforming business operations across multiple domains. "
        "Document intelligence allows automated extraction of valuable data from invoices and receipts. "
        "Retrieval-Augmented Generation bridges the gap between static LLMs and dynamic private company knowledge. "
        "Vector search leverages embedding spaces to retrieve high-semantic-accuracy context."
    )
    pages = [ParsedPage(page_number=1, text=text, metadata={"test": True})]
    doc = ParsedDocument(filename="ai_doc.txt", file_type="txt", total_pages=1, pages=pages, metadata={})

    chunks = chunker.chunk_document("doc_123", doc)
    assert len(chunks) > 1
    for c in chunks:
        assert c["document_id"] == "doc_123"
        assert c["filename"] == "ai_doc.txt"
        assert c["page_number"] == 1
        assert len(c["text"]) > 0

def test_chunking_short_document():
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    pages = [ParsedPage(page_number=1, text="Short content.", metadata={})]
    doc = ParsedDocument(filename="short.txt", file_type="txt", total_pages=1, pages=pages, metadata={})

    chunks = chunker.chunk_document("doc_short", doc)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short content."
