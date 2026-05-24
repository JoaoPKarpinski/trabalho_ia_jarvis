from __future__ import annotations

import os
from pathlib import Path
from typing import List, Sequence

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = Path(__file__).resolve().parents[1] / "data" / "chroma_db"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


class SentenceTransformerEmbeddingFunction:
    def __init__(self, model_name: str) -> None:
        self._model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed_documents(input)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        cleaned = [str(text) for text in texts]
        if not cleaned:
            return []
        embeddings = self._model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(
        self,
        text: str | None = None,
        input: str | Sequence[str] | None = None,
    ) -> List[List[float]]:
        query = input if input is not None else text
        if isinstance(query, Sequence) and not isinstance(query, str):
            texts = [str(item) for item in query]
        else:
            texts = [str(query or "")]

        if not texts:
            return []

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()
    
    def name(self) -> str:
        return "sentence_transformer_custom"


_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
_embedding_fn = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL)
_collection = None


def get_collection():
    global _collection
    if _collection is None:
        _collection = _client.get_or_create_collection(
            name="jarvis_docs",
            embedding_function=_embedding_fn,
        )
    return _collection
