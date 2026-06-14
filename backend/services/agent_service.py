from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from services.agenda_service import agenda_as_text
from services.rag_service import search_documents
from services.task_service import complete_task, create_task, delete_task, list_tasks, update_task

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://llm.liaufms.org/v1/gemma-3-12b-it"
DEFAULT_MODEL = "google/gemma-3-12b-it"
DEFAULT_TOOL_MODE = "wrapper"

SYSTEM_PROMPT_AUTO = (
    "You are Jarvis, an academic assistant. "
    "Respond in Brazilian Portuguese and keep answers concise."
)

TOOLS = [
    "search_documents, to search for relevant document context based on a query. Arguments: query (str), top_k (int, optional)",
    "get_agenda, to retrieve the user's agenda. Arguments: None",
    "add_task, to add a new task. Arguments: title (str), description (str, optional)",
    "list_tasks, to list all tasks. Arguments: None",
    "complete_task, to mark a task as complete. Arguments: task_id (int)",
    "update_task, to update an existing task. Arguments: task_id (int), title (str, optional), description (str, optional)",
    "delete_task, to delete a task. Arguments: task_id (int)",
]

TOOL_CALLING_PROMPT = (
    "Based on the user's message, the conversation context and the available local tools, decide if you need to call a tool to answer or perform the requested operation. "
    "The available tools are:" + ";".join(TOOLS) + ". "
    "Prefer search_documents every time the message relates to academic, technical or work/job related subject, and whenever the user request may depend on uploaded or indexed documents. "
    "Respond only with JSON in the following format: {\"tool\": \"tool_name\", \"arguments\": {\"arg1\": \"value1\", \"arg2\": \"value2\"}}. "
    "If no tool is needed, respond only with {\"tool\": null, \"arguments\": {}}. "
)

TOOL_RESPONSE_PROMPT = (
    "You have called a tool and received the following response: {tool_response}. "
    "The value returned from the called tool is: {tool_result}. "
    "Use this information to help answer the user's question. "
    "If you need to call another tool, respond with the JSON format mentioned before. "
    "If you have enough information to answer the question, provide a concise answer in Brazilian Portuguese."
)

SYSTEM_PROMPT_MANUAL = (
    "You are Jarvis, an academic assistant. "
    "You will receive document context already retrieved. "
    "Do not ask to call tools and do not output tool code. "
    "If the document context is empty, say you could not find relevant info locally and answer with your own knowledge. "
    "Respond in Brazilian Portuguese and keep answers concise."
)

def run_agent(message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    client = _get_client()
    messages = _normalize_history(history or [])
    return orchestrate_operations(client, messages, message)


def orchestrate_operations(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    message: str,
) -> str:
    working_messages = list(messages)
    accumulated_context: List[str] = []

    for _ in range(3):
        tool_call = _request_tool_call(client, working_messages, message, accumulated_context)
        if tool_call is None:
            return _generate_final_answer(client, working_messages, message, accumulated_context)

        tool_name = tool_call["tool"]
        tool_arguments = tool_call["arguments"]
        tool_result = _dispatch_tool(tool_name, json.dumps(tool_arguments, ensure_ascii=True))
        accumulated_context.append(_format_tool_result(tool_name, tool_arguments, tool_result))

    return _generate_final_answer(client, working_messages, message, accumulated_context)


def _get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set. Create a .env file.")
    return OpenAI(base_url=base_url, api_key=api_key)


def _get_model() -> str:
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)

def _append_user_message(messages: List[Dict[str, Any]], content: str) -> None:
    if not content:
        return
    if messages and messages[-1].get("role") == "user":
        messages[-1]["content"] += "\n\n" + content
    else:
        messages.append({"role": "user", "content": content})


def _normalize_history(history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in history:
        role = item.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = (item.get("content") or "").strip()
        if not content:
            continue

        if not normalized and role == "assistant": # primeira mensagem
            continue
        if normalized and normalized[-1]["role"] == role: # se a lista está preenchida e a última mensagem é do role do item atual. Caso difícil de acontecer
            normalized[-1]["content"] += "\n\n" + content
        else:
            normalized.append({"role": role, "content": content})

    return normalized


def _request_tool_call(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    message: str,
    accumulated_context: List[str],
) -> Optional[Dict[str, Any]]:
    prompt_parts = [TOOL_CALLING_PROMPT]
    if accumulated_context:
        prompt_parts.append("Contexto já recuperado:\n" + "\n\n".join(accumulated_context))
    prompt_parts.append("Mensagem do usuário:\n" + message)
    prompt = "\n\n".join(prompt_parts)

    planner_messages = list(messages)
    planner_messages.append({"role": "user", "content": prompt})

    logger.info("[LLM][planner] prompt enviado:\n%s", _truncate_for_log(str(planner_messages)))
    response = client.chat.completions.create(
        model=_get_model(),
        messages=planner_messages,
        temperature=0.0,
    )
    content = response.choices[0].message.content or ""
    logger.info("[LLM][planner] resposta bruta:\n%s", _truncate_for_log(content))
    return _parse_tool_call(content)


def _generate_final_answer(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    message: str,
    accumulated_context: List[str],
) -> str:
    prompt_parts = [SYSTEM_PROMPT_MANUAL]
    if accumulated_context:
        prompt_parts.append("Contexto recuperado pelas ferramentas:\n" + "\n\n".join(accumulated_context))
    prompt_parts.append("Mensagem do usuário:\n" + message)
    prompt = "\n\n".join(prompt_parts)

    logger.info("[LLM][final] prompt enviado:\n%s", _truncate_for_log(prompt))

    answer_messages = list(messages)
    answer_messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=_get_model(),
        messages=answer_messages,
        temperature=0.2,
    )
    content = response.choices[0].message.content or ""
    logger.info("[LLM][final] resposta bruta:\n%s", _truncate_for_log(content))
    return content


def _format_tool_result(tool_name: str, tool_arguments: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
    return (
        f"Ferramenta executada: {tool_name}\n"
        f"Argumentos: {json.dumps(tool_arguments, ensure_ascii=True)}\n"
        f"Resultado: {json.dumps(tool_result, ensure_ascii=True)}"
    )


def _parse_tool_call(content: str) -> Optional[Dict[str, Any]]:
    raw_content = (content or "").strip()
    if not raw_content:
        return None

    candidate = _extract_json_object(raw_content)
    if candidate is None:
        return None

    tool_name = candidate.get("tool") or candidate.get("name")
    if isinstance(tool_name, dict):
        tool_name = tool_name.get("name") or tool_name.get("tool")

    if not tool_name:
        return None

    normalized_tool = str(tool_name).strip()
    if normalized_tool.lower() in {"none", "null", "nada", "sem_tool", "no_tool"}:
        return None

    arguments = candidate.get("arguments") or candidate.get("args") or {}
    if not isinstance(arguments, dict):
        arguments = {}

    return {"tool": normalized_tool, "arguments": arguments}


def _extract_json_object(content: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    snippet = content[start : end + 1]
    try:
        parsed = json.loads(snippet)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None

    return None


def _dispatch_tool(name: str, raw_arguments: str) -> Dict[str, Any]:
    try:
        arguments = json.loads(raw_arguments) if raw_arguments else {}
    except json.JSONDecodeError:
        arguments = {}

    logger.info("[TOOL] executando %s com argumentos: %s", name, _truncate_for_log(json.dumps(arguments, ensure_ascii=True)))

    try:
        if name == "search_documents":
            query = str(arguments.get("query", ""))
            top_k = int(arguments.get("top_k", 4))
            result = search_documents(query=query, top_k=top_k)
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
        if name == "get_agenda":
            result = {"agenda": agenda_as_text()}
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
        if name == "add_task":
            result = create_task(
                title=str(arguments.get("title", "")),
                description=arguments.get("description"),
                due_date=arguments.get("due_date"),
            )
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
        if name == "list_tasks":
            include_completed = bool(arguments.get("include_completed", True))
            result = {"tasks": list_tasks(include_completed=include_completed)}
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
        if name == "complete_task": # to-do: fazer com que busque por nome da tarefa também
            task_id = int(arguments.get("task_id"))
            completed = bool(arguments.get("completed", True))
            result = complete_task(task_id=task_id, completed=completed) or {"error": "Task not found"}
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
        if name == "update_task":
            task_id = int(arguments.get("task_id"))
            result = update_task(
                task_id=task_id,
                title=arguments.get("title"),
                description=arguments.get("description"),
                due_date=arguments.get("due_date"),
                completed=arguments.get("completed"),
            ) or {"error": "Task not found"}
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
        if name == "delete_task":
            task_id = int(arguments.get("task_id"))
            result = {"deleted": delete_task(task_id)}
            logger.info("[TOOL] resultado de %s: %s", name, _truncate_for_log(json.dumps(result, ensure_ascii=True)))
            return result
    except Exception as exc:
        logger.exception("[TOOL] erro executando %s", name)
        return {"error": str(exc)}

    logger.warning("[TOOL] ferramenta desconhecida: %s", name)
    return {"error": f"Unknown tool: {name}"}


def _truncate_for_log(value: str, limit: int = 2000) -> str:
    if len(value) <= limit:
        return value
    return "... [truncated]" + value[limit:]
