from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.quiz_service import generate_quiz

router = APIRouter()


class QuizRequest(BaseModel):
    topic: Optional[str] = None
    num_questions: int = Field(default=3, ge=1, le=20)
    difficulty: str = Field(default="médio", pattern="^(fácil|médio|difícil)$")


@router.post("/quiz/generate")
def quiz_generate(payload: QuizRequest) -> Dict[str, Any]:
    try:
        return generate_quiz(
            topic=payload.topic,
            num_questions=payload.num_questions,
            difficulty=payload.difficulty,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))