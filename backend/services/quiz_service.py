from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from services.rag_service import search_documents

DEFAULT_BASE_URL = "https://llm.liaufms.org/v1/gemma-3-12b-it"
DEFAULT_MODEL = "google/gemma-3-12b-it"

QUIZ_SYSTEM_PROMPT = (
    "Você é um gerador de provas acadêmicas chamado Jarvis. "
    "Gere apenas questões objetivas, coerentes com o contexto recuperado. "
    "Responda exclusivamente com JSON puro, sem markdown, sem explicações fora do JSON e sem texto extra. "
    "A resposta deve seguir exatamente este formato: "
    "{\"exercicios\":[{\"pergunta\":\"...\",\"opcoes\":[\"...\",\"...\",\"...\",\"...\"],\"indice_correto\":1,\"justificativa\":\"...\",\"referencia_fonte\":\"[documento.pdf#3]\"}]}. "
    "Crie exatamente a quantidade solicitada de exercícios. "
    "O campo indice_correto deve ser um inteiro entre 0 e 3. "
    "A referencia_fonte deve apontar para a string exata da fonte recuperada no contexto."
)


def generate_quiz(topic: Optional[str], num_questions: int, difficulty: str) -> Dict[str, Any]:
    client = _get_client()
    query = (topic or "estudos").strip() or "estudos"
    top_k = max(num_questions * 2, 4)
    retrieved = search_documents(query=query, top_k=top_k)
    context = str(retrieved.get("context", "")).strip()
    sources = retrieved.get("sources", [])

    user_prompt = _build_user_prompt(query=query, num_questions=num_questions, difficulty=difficulty, context=context, sources=sources)
    response = client.chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    raw_content = response.choices[0].message.content or ""
    parsed = _parse_json_object(raw_content)
    if parsed is None:
        return {
            "erro": "LLM retornou JSON malformado",
            "raw": _truncate(raw_content),
        }

    return _normalize_quiz_payload(parsed)


def _get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set. Create a .env file.")
    return OpenAI(base_url=base_url, api_key=api_key)


def _get_model() -> str:
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)


def _build_user_prompt(
    query: str,
    num_questions: int,
    difficulty: str,
    context: str,
    sources: List[Dict[str, Any]],
) -> str:
    source_lines = []
    for item in sources:
        if isinstance(item, dict):
            source = item.get("source", "document")
            chunk = item.get("chunk", 0)
            source_lines.append(f"[{source}#{chunk}]")

    source_block = "\n".join(source_lines) if source_lines else "[documento#0]"
    context_block = context if context else "(sem contexto recuperado)"

    return (
        f"Tema: {query}\n"
        f"Quantidade de questões: {num_questions}\n"
        f"Dificuldade: {difficulty}\n\n"
        f"Fontes recuperadas:\n{source_block}\n\n"
        f"Contexto recuperado:\n{context_block}\n\n"
        "Produza somente o JSON final no formato especificado."
    )


def _parse_json_object(content: str) -> Optional[Dict[str, Any]]:
    raw_content = (content or "").strip()
    if not raw_content:
        return None

    try:
        parsed = json.loads(raw_content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = raw_content.find("{")
    end = raw_content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(raw_content[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None

    return None


def _normalize_quiz_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    exercises = payload.get("exercicios", [])
    if not isinstance(exercises, list):
        exercises = []

    normalized: List[Dict[str, Any]] = []
    for item in exercises:
        if not isinstance(item, dict):
            continue
        options = item.get("opcoes", [])
        if not isinstance(options, list):
            options = []
        normalized.append(
            {
                "pergunta": str(item.get("pergunta", "")).strip(),
                "opcoes": [str(option) for option in options[:4]],
                "indice_correto": item.get("indice_correto", 0),
                "justificativa": str(item.get("justificativa", "")).strip(),
                "referencia_fonte": str(item.get("referencia_fonte", "")).strip(),
            }
        )

    return {"exercicios": normalized}


def _truncate(value: str, limit: int = 2000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "... [truncated]"