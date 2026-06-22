from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from services.rag_service import search_documents

load_dotenv()

DEFAULT_BASE_URL = "https://llm.liaufms.org/v1/gemma-3-12b-it"
DEFAULT_MODEL = "google/gemma-3-12b-it"

QUESTION_SYSTEM_PROMPT = (
    "Você é um gerador de perguntas acadêmicas rigoroso. "
    "Responda somente com JSON puro, sem markdown, sem comentários e sem texto adicional. "
    "Crie exatamente UMA pergunta dissertativa, em português do Brasil. "
    "A estrutura obrigatória é: {\"pergunta\":\"...\",\"resposta_esperada\":\"...\",\"referencia_fonte\":\"[documento.pdf#3]\"}. "
    "A pergunta deve exigir explicação, análise ou desenvolvimento, e não deve ser de múltipla escolha. "
    "A resposta_esperada deve ser objetiva e servir como gabarito interno. "
    "A referencia_fonte deve ser uma string exata presente no contexto recuperado. "
    "Evite repetir perguntas já feitas na sessão."
)

EVALUATION_SYSTEM_PROMPT = (
    "Você é um avaliador acadêmico rigoroso. "
    "Responda somente com JSON puro, sem markdown, sem comentários e sem texto adicional. "
    "Avalie se a resposta do usuário corresponde à questão dissertativa atual. "
    "A estrutura obrigatória é: {\"correta\":true,\"explicacao\":\"...\",\"referencia_fonte\":\"[documento.pdf#3]\"}. "
    "Se a resposta estiver errada, explique o motivo de forma objetiva, cite a referência de fonte fornecida no contexto e proponha o direcionamento correto."
)

SUMMARY_SYSTEM_PROMPT = (
    "Você é um analista de desempenho acadêmico. "
    "Responda somente com JSON puro, sem markdown, sem comentários e sem texto adicional. "
    "Produza uma síntese da sessão e indique pontos de estudo prioritários. "
    "A estrutura obrigatória é: {\"sintese\":\"...\",\"desempenho\":\"...\",\"pontos_foco\":[\"...\",\"...\"]}."
)

END_SESSION_PATTERNS = (
    r"\bencerrar\b",
    r"\bencerra\b",
    r"\bfinalizar\b",
    r"\bfim da sess[aã]o\b",
    r"\bterminar\b",
    r"\bsair\b",
    r"\bclose\b",
)

SESSION_STORE: Dict[str, "StudySession"] = {}


@dataclass
class StudySession:
    session_id: str
    topic: str
    context: str
    sources: List[Dict[str, Any]]
    current_question: Optional[Dict[str, Any]] = None
    question_history: List[Dict[str, Any]] = field(default_factory=list)
    answer_history: List[Dict[str, Any]] = field(default_factory=list)
    correct_answers: int = 0
    total_answers: int = 0
    active: bool = True


def handle_study_message(session_id: Optional[str], message: str) -> Dict[str, Any]:
    cleaned_message = (message or "").strip()
    if not cleaned_message:
        raise ValueError("message is required")

    if session_id and session_id in SESSION_STORE:
        session = SESSION_STORE[session_id]
        if _is_end_message(cleaned_message):
            return _end_session(session)
        if session.current_question is None:
            session.current_question = _generate_question(session)
            session.question_history.append(session.current_question)
            return _build_response(session, _compose_question_message(session, "Sessão retomada."), status="awaiting_answer")
        return _evaluate_answer_and_continue(session, cleaned_message)

    return _start_session(cleaned_message)


def _start_session(topic: str) -> Dict[str, Any]:
    session = _create_session(topic)
    first_question = _generate_question(session)
    session.current_question = first_question
    session.question_history.append(first_question)
    SESSION_STORE[session.session_id] = session
    return _build_response(session, _compose_question_message(session, "Sessão iniciada. Responda à pergunta abaixo."), status="awaiting_answer")


def _evaluate_answer_and_continue(session: StudySession, user_answer: str) -> Dict[str, Any]:
    question = session.current_question or _generate_question(session)
    evaluation = _evaluate_answer(session, question, user_answer)

    session.total_answers += 1
    if evaluation.get("correta"):
        session.correct_answers += 1

    session.answer_history.append(
        {
            "pergunta": question,
            "resposta_usuario": user_answer,
            "avaliacao": evaluation,
        }
    )

    next_question = _generate_question(session, previous_answer=user_answer, previous_evaluation=evaluation)
    session.current_question = next_question
    session.question_history.append(next_question)

    feedback = _compose_feedback_message(session, question, evaluation)
    next_prompt = _compose_question_message(session, "Agora responda à próxima pergunta.")
    return _build_response(
        session,
        f"{feedback}\n\n{next_prompt}",
        status="awaiting_answer",
    )


def _end_session(session: StudySession) -> Dict[str, Any]:
    summary = _generate_summary(session)
    session.active = False
    SESSION_STORE.pop(session.session_id, None)
    return _build_response(
        session,
        _compose_summary_message(session, summary),
        status="completed",
    )


def _create_session(topic: str) -> StudySession:
    retrieved = search_documents(query=topic or "estudos", top_k=6)
    context = str(retrieved.get("context", "")).strip()
    sources = retrieved.get("sources", []) if isinstance(retrieved.get("sources", []), list) else []
    return StudySession(
        session_id=uuid.uuid4().hex,
        topic=topic,
        context=context,
        sources=sources,
    )


def _generate_question(
    session: StudySession,
    previous_answer: Optional[str] = None,
    previous_evaluation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    client = _get_client()
    prompt_parts = [
        f"Tópico da sessão: {session.topic}",
        f"Contexto recuperado:\n{session.context or '(sem contexto recuperado)'}",
        f"Fontes recuperadas:\n{_format_sources(session.sources)}",
        f"Quantidade de perguntas já feitas: {len(session.question_history)}",
    ]
    if previous_answer is not None:
        prompt_parts.append(f"Resposta anterior do usuário: {previous_answer}")
    if previous_evaluation is not None:
        prompt_parts.append(f"Avaliação anterior: {json.dumps(previous_evaluation, ensure_ascii=True)}")

    prompt_parts.append("Gere uma nova pergunta dissertativa diferente das anteriores e use uma fonte recuperada no campo referencia_fonte.")
    raw_content = _call_llm(client, QUESTION_SYSTEM_PROMPT, "\n\n".join(prompt_parts))
    parsed = _parse_json_object(raw_content)
    if parsed is None:
        return _fallback_question(session)

    return _normalize_question_payload(parsed, session)


def _evaluate_answer(session: StudySession, question: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
    client = _get_client()
    prompt = (
        f"Tópico da sessão: {session.topic}\n\n"
        f"Contexto recuperado:\n{session.context or '(sem contexto recuperado)'}\n\n"
        f"Questão atual:\n{question.get('pergunta', '')}\n\n"
        f"Resposta do usuário:\n{user_answer}\n\n"
        "Avalie a resposta e responda somente no JSON exigido."
    )
    raw_content = _call_llm(client, EVALUATION_SYSTEM_PROMPT, prompt)
    parsed = _parse_json_object(raw_content)
    if parsed is None:
        return _fallback_evaluation(question, user_answer)

    normalized = _normalize_evaluation_payload(parsed, question)
    if normalized.get("correta") is None:
        normalized["correta"] = _infer_answer_correctness(question, user_answer)
    return normalized


def _generate_summary(session: StudySession) -> Dict[str, Any]:
    client = _get_client()
    prompt = (
        f"Tópico da sessão: {session.topic}\n\n"
        f"Contexto recuperado:\n{session.context or '(sem contexto recuperado)'}\n\n"
        f"Histórico das perguntas e respostas:\n{json.dumps(session.answer_history, ensure_ascii=True)}\n\n"
        f"Estatísticas da sessão:\n{json.dumps(_session_stats(session), ensure_ascii=True)}\n\n"
        "Gere a síntese e os pontos de foco no formato JSON exigido."
    )
    raw_content = _call_llm(client, SUMMARY_SYSTEM_PROMPT, prompt)
    parsed = _parse_json_object(raw_content)
    if parsed is None:
        return _fallback_summary(session)

    return _normalize_summary_payload(parsed, session)


def _call_llm(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set. Create a .env file.")
    return OpenAI(base_url=base_url, api_key=api_key)


def _get_model() -> str:
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)


def _build_response(session: StudySession, jarvis_message: str, status: str) -> Dict[str, Any]:
    return {
        "session_id": session.session_id,
        "status": status,
        "topic": session.topic,
        "jarvis_message": jarvis_message,
    }


def _compose_question_message(session: StudySession, prefix: str) -> str:
    question = session.current_question or {}
    question_text = str(question.get("pergunta", "")).strip()
    if not question_text:
        question_text = "Pergunta indisponível no momento."
    return f"{prefix} {question_text}"


def _compose_feedback_message(session: StudySession, question: Dict[str, Any], evaluation: Dict[str, Any]) -> str:
    expected_answer = str(question.get("resposta_esperada", "")).strip()
    reference = str(evaluation.get("referencia_fonte") or question.get("referencia_fonte", "")).strip()

    if evaluation.get("correta"):
        return (
            "Você respondeu corretamente. "
            f"{str(evaluation.get('explicacao', '')).strip()}"
        ).strip()

    parts = [
        "Você ainda não chegou à resposta correta.",
        f"A resposta esperada é: {expected_answer}." if expected_answer else "",
        f"Referência utilizada: {reference}." if reference else "",
        str(evaluation.get("explicacao", "")).strip(),
    ]
    return " ".join(part for part in parts if part).strip()


def _compose_summary_message(session: StudySession, summary: Dict[str, Any]) -> str:
    sintese = str(summary.get("sintese", "")).strip() or _fallback_summary(session)["sintese"]
    desempenho = str(summary.get("desempenho", "")).strip() or _performance_label(session)
    pontos = summary.get("pontos_foco", [])
    if not isinstance(pontos, list):
        pontos = []
    pontos_text = "; ".join(str(item).strip() for item in pontos if str(item).strip())
    if not pontos_text:
        pontos_text = _performance_focus(session)

    return (
        f"Sessão encerrada. {sintese} "
        f"Análise do desempenho: {desempenho} "
        f"Pontos para focar nos estudos: {pontos_text}."
    ).strip()


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


def _normalize_question_payload(payload: Dict[str, Any], session: StudySession) -> Dict[str, Any]:
    reference = str(payload.get("referencia_fonte", "")).strip()
    if not reference:
        reference = _first_source_reference(session.sources)

    return {
        "pergunta": str(payload.get("pergunta", "")).strip() or "Pergunta indisponível.",
        "resposta_esperada": str(payload.get("resposta_esperada", "")).strip() or "Resposta esperada indisponível.",
        "referencia_fonte": reference,
    }


def _normalize_evaluation_payload(payload: Dict[str, Any], question: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "correta": bool(payload.get("correta", False)),
        "explicacao": str(payload.get("explicacao", "")).strip() or "Não foi possível gerar a explicação.",
        "referencia_fonte": str(payload.get("referencia_fonte", question.get("referencia_fonte", ""))).strip(),
    }


def _normalize_summary_payload(payload: Dict[str, Any], session: StudySession) -> Dict[str, Any]:
    referencias = payload.get("referencias_utilizadas", [])
    if not isinstance(referencias, list):
        referencias = []

    return {
        "sintese": str(payload.get("sintese", "")).strip() or "Sessão concluída.",
        "desempenho": str(payload.get("desempenho", "")).strip() or _performance_label(session),
        "pontos_foco": [str(item).strip() for item in payload.get("pontos_foco", []) if str(item).strip()] if isinstance(payload.get("pontos_foco", []), list) else [_performance_focus(session)],
        "referencias_utilizadas": [str(item).strip() for item in referencias if str(item).strip()],
    }


def _fallback_question(session: StudySession) -> Dict[str, Any]:
    reference = _first_source_reference(session.sources)
    return {
        "pergunta": f"Explique como o tema {session.topic} se relaciona com o contexto estudado e apresente os principais elementos envolvidos.",
        "resposta_esperada": "A resposta deve demonstrar compreensão conceitual, relacionar o tema ao contexto e citar os elementos centrais do conteúdo recuperado.",
        "referencia_fonte": reference,
    }


def _fallback_evaluation(question: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
    return {
        "correta": False,
        "explicacao": "Não foi possível avaliar a resposta com segurança no modo de fallback. Refaça a explicação com base no tema e no contexto recuperado.",
        "referencia_fonte": str(question.get("referencia_fonte", "")).strip(),
    }


def _fallback_summary(session: StudySession) -> Dict[str, Any]:
    return {
        "sintese": f"Sessão sobre {session.topic} concluída com {session.correct_answers} acertos em {session.total_answers} respostas.",
        "desempenho": _performance_label(session),
        "pontos_foco": [_performance_focus(session)],
        "referencias_utilizadas": [_first_source_reference(session.sources)] if session.sources else [],
    }


def _infer_answer_correctness(question: Dict[str, Any], user_answer: str) -> bool:
    normalized_answer = (user_answer or "").strip().lower()
    expected = str(question.get("resposta_esperada", "")).strip().lower()
    if not normalized_answer or not expected:
        return False
    if normalized_answer == expected:
        return True
    expected_keywords = [word for word in re.split(r"\W+", expected) if len(word) > 3]
    if not expected_keywords:
        return False
    matches = sum(1 for word in expected_keywords if word in normalized_answer)
    return matches >= max(1, len(expected_keywords) // 2)


def _session_stats(session: StudySession) -> Dict[str, Any]:
    accuracy = round((session.correct_answers / session.total_answers) * 100, 2) if session.total_answers else 0.0
    return {
        "correct_answers": session.correct_answers,
        "total_answers": session.total_answers,
        "accuracy": accuracy,
    }


def _performance_label(session: StudySession) -> str:
    if session.total_answers == 0:
        return "Sem respostas avaliadas ainda."
    accuracy = session.correct_answers / session.total_answers
    if accuracy >= 0.85:
        return "Desempenho excelente."
    if accuracy >= 0.6:
        return "Desempenho satisfatório, com espaço para refinamento."
    return "Desempenho abaixo do esperado, exigindo revisão dos fundamentos."


def _performance_focus(session: StudySession) -> str:
    if session.total_answers == 0:
        return f"Revisar os fundamentos de {session.topic} antes de continuar."
    if session.correct_answers < session.total_answers:
        return f"Reforçar os pontos em que houve erro no tema {session.topic}."
    return f"Avançar para tópicos mais específicos de {session.topic}."


def _first_source_reference(sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "[documento#0]"
    source = sources[0] if isinstance(sources[0], dict) else {}
    source_name = str(source.get("source", "documento")).strip() or "documento"
    chunk = source.get("chunk", 0)
    return f"[{source_name}#{chunk}]"


def _format_sources(sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "[documento#0]"
    lines: List[str] = []
    for item in sources:
        if isinstance(item, dict):
            source_name = str(item.get("source", "documento")).strip() or "documento"
            chunk = item.get("chunk", 0)
            lines.append(f"[{source_name}#{chunk}]")
    return "\n".join(lines) if lines else "[documento#0]"


def _is_end_message(message: str) -> bool:
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in END_SESSION_PATTERNS)