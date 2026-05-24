from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.rag_service import ingest_document

router = APIRouter()


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, int]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    file_name = file.filename or "document"
    content_type = file.content_type or ""
    return ingest_document(file_name=file_name, content_type=content_type, file_bytes=content)
