from __future__ import annotations

import logging
import os
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Sequence

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHROMA_PATH = Path(__file__).resolve().parents[1] / "data" / "chroma_db"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = "jarvis_docs"

_LOCK = threading.Lock()
_client = None
_embedding_fn = None
_collection = None


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


def _create_client():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def _get_embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL)
    return _embedding_fn


def _get_client():
    global _client
    if _client is None:
        _client = _create_client()
    return _client


def _reset_storage() -> None:
    global _client, _collection

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = CHROMA_PATH.with_name(f"{CHROMA_PATH.name}.broken-{timestamp}")

    if CHROMA_PATH.exists():
        logger.warning("Chroma store inconsistente detectado. Movendo para %s", backup_path)
        shutil.move(str(CHROMA_PATH), str(backup_path))

    _client = _create_client()
    _collection = None


def repair_collection_storage() -> None:
    with _LOCK:
        _reset_storage()


def get_collection():
    global _collection
    with _LOCK:
        if _collection is None:
            try:
                _collection = _get_client().get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=_get_embedding_function(),
                )
            except Exception:
                _reset_storage()
                _collection = _get_client().get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=_get_embedding_function(),
                )
        return _collection
