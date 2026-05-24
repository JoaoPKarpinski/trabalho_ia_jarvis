from __future__ import annotations

import io
import uuid
from typing import Dict, List, Tuple

from pypdf import PdfReader

from database.vector_manager import get_collection


def ingest_document(file_name: str, content_type: str, file_bytes: bytes) -> Dict[str, int]:
    text = _extract_text(file_name, content_type, file_bytes)
    chunks = _split_text(text)
    if not chunks:
        return {"chunks_added": 0}

    collection = get_collection()
    ids = [f"{file_name}-{idx}-{uuid.uuid4().hex}" for idx in range(len(chunks))]
    metadatas = [{"source": file_name, "chunk": idx} for idx in range(len(chunks))]
    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    return {"chunks_added": len(chunks)}


def search_documents(query: str, top_k: int = 4) -> Dict[str, object]:
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    context_parts: List[str] = []
    sources: List[Dict[str, object]] = []
    for doc, meta in zip(documents, metadatas):
        source = meta.get("source", "document") if isinstance(meta, dict) else "document"
        chunk = meta.get("chunk", 0) if isinstance(meta, dict) else 0
        context_parts.append(f"[{source}#{chunk}]\n{doc}")
        sources.append({"source": source, "chunk": chunk})

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources,
    }


def _extract_text(file_name: str, content_type: str, file_bytes: bytes) -> str:
    if content_type == "application/pdf" or file_name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    return file_bytes.decode("utf-8", errors="ignore")


def _split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    if chunk_size <= chunk_overlap:
        raise ValueError("chunk_size must be larger than chunk_overlap")

    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []

    words = cleaned.split()
    
    chunks: List[str] = []
    current_chunk_words: List[str] = []
    current_length = 0
    
    for word in words:
        word_len = len(word) + 1 
        
        if current_length + word_len > chunk_size and current_chunk_words:
            chunks.append(" ".join(current_chunk_words))
            
            overlap_words = []
            overlap_length = 0
            
            for w in reversed(current_chunk_words):
                if overlap_length + len(w) + 1 <= chunk_overlap:
                    overlap_words.insert(0, w)
                    overlap_length += len(w) + 1
                else:
                    break

            current_chunk_words = overlap_words
            current_length = overlap_length
        
        current_chunk_words.append(word)
        current_length += word_len

    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))

    return chunks
