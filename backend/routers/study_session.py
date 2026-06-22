from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.study_session_service import handle_study_message

router = APIRouter()


class StudySessionRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)


@router.post("/study/session/message")
def study_session_message(payload: StudySessionRequest) -> Dict[str, Any]:
    try:
        return handle_study_message(session_id=payload.session_id, message=payload.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))