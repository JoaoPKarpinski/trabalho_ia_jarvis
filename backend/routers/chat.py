from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agent_service import run_agent

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


@router.post("/chat")
def chat(payload: ChatRequest) -> Dict[str, str]:
    try:
        history = [item.model_dump() for item in payload.history] if payload.history else None
        reply = run_agent(payload.message, history=history)
        return {"reply": reply}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
