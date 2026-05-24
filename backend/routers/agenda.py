from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.agenda_service import agenda_as_text, save_agenda

router = APIRouter()


@router.post("/agenda/upload")
async def upload_agenda(file: UploadFile = File(...)) -> Dict[str, str]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    save_agenda(content)
    return {"status": "ok"}


@router.get("/agenda/text")
def get_agenda_text() -> Dict[str, str]:
    return {"text": agenda_as_text()}
