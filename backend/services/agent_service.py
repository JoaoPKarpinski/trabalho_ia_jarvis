from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from services.agenda_service import agenda_as_text
from services.rag_service import search_documents
from services.task_service import complete_task, create_task, delete_task, list_tasks, update_task

load_dotenv()

DEFAULT_BASE_URL = "https://llm.liaufms.org/v1/gemma-3-12b-it"
DEFAULT_MODEL = "google/gemma-3-12b-it"
DEFAULT_TOOL_MODE = "manual"

SYSTEM_PROMPT_AUTO = (
    "You are Jarvis, an academic assistant. "
    "Use tools to fetch study materials (RAG), read the agenda, and manage tasks. "
    "If a question needs document context, call the search_documents tool first. "
    "If a question is about schedule, call the get_agenda tool. "
    "If a question is about tasks, call the task tools. "
    "Respond in Brazilian Portuguese and keep answers concise."
)

SYSTEM_PROMPT_MANUAL = (
    "You are Jarvis, an academic assistant. "
    "You will receive document context already retrieved. "
    "Do not ask to call tools and do not output tool code. "
    "If the document context is empty, say you could not find relevant info locally and answer with your own knowledge. "
    "Respond in Brazilian Portuguese and keep answers concise."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search study materials and return relevant context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 4},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_agenda",
            "description": "Return the current agenda as text.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a task to the task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_completed": {"type": "boolean", "default": True}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed or not completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "completed": {"type": "boolean", "default": True},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update task fields.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string"},
                    "completed": {"type": "boolean"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    },
]


def run_agent(message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    client = _get_client()
    messages = _normalize_history(history or [])

    tool_mode = _get_tool_mode()
    if tool_mode == "auto":
        system_context = _get_system_context(message, include_context=False)
        return _run_agent_with_tools(client, messages, message, system_context)
    system_context = _get_system_context(message, include_context=True)
    return _run_agent_manual(client, messages, message, system_context)


def _run_agent_with_tools(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    message: str,
    system_context: str,
) -> str:
    _apply_system_context(messages, system_context)
    _append_user_message(messages, message)

    for _ in range(2):
        response = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )
        reply = response.choices[0].message
        tool_calls = reply.tool_calls or []

        if not tool_calls:
            return reply.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": reply.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": call.type,
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )

        for call in tool_calls:
            result = _dispatch_tool(call.function.name, call.function.arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=True),
                }
            )

    return "Desculpe, nao consegui completar a resposta agora."


def _run_agent_manual(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    message: str,
    system_context: str,
) -> str:
    _apply_system_context(messages, system_context)
    _append_user_message(messages, message)
    response = client.chat.completions.create(
        model=_get_model(),
        messages=messages,
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


def _get_tool_mode() -> str:
    mode = os.getenv("LLM_TOOL_MODE", DEFAULT_TOOL_MODE).strip().lower()
    if mode not in {"auto", "manual"}:
        return DEFAULT_TOOL_MODE
    return mode


def _get_system_context(message: str, include_context: bool) -> str:
    prompt = SYSTEM_PROMPT_MANUAL if include_context else SYSTEM_PROMPT_AUTO
    if not include_context:
        return prompt
    context = _build_context(message)
    if context:
        return prompt + "\n\n" + context
    return prompt


def _apply_system_context(messages: List[Dict[str, Any]], system_context: str) -> None:
    if not system_context:
        return

    for item in messages:
        if item.get("role") == "user":
            item["content"] = system_context + "\n\n" + item.get("content", "")
            return

    messages.insert(0, {"role": "user", "content": system_context})


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


def _build_context(message: str) -> str:
    message_lower = message.lower()
    blocks: List[str] = []

    rag = search_documents(query=message, top_k=4)
    doc_context = rag.get("context", "")
    if doc_context:
        blocks.append("Contexto de documentos:\n" + doc_context)
    else:
        blocks.append("Contexto de documentos:\n(vazio)")

    if _should_use_agenda(message_lower):
        agenda_text = agenda_as_text()
        if agenda_text:
            blocks.append("Agenda:\n" + agenda_text)

    if _should_use_tasks(message_lower):
        tasks = list_tasks(include_completed=True)
        blocks.append("Tarefas:\n" + json.dumps(tasks, ensure_ascii=True))

    return "\n\n".join(blocks)


def _should_use_documents(message_lower: str) -> bool:
    keywords = (
        "document",
        "material",
        "pdf",
        "resum",
        "conteudo",
        "capitulo",
        "trecho",
        "anot",
        "slide",
        "apostila",
        "livro",
        "texto",
    )
    return any(keyword in message_lower for keyword in keywords)


def _should_use_agenda(message_lower: str) -> bool:
    keywords = (
        "agenda",
        "aula",
        "prova",
        "hoje",
        "amanha",
        "semana",
        "horario",
        "horarios",
        "calendario",
        "compromisso",
    )
    return any(keyword in message_lower for keyword in keywords)


def _should_use_tasks(message_lower: str) -> bool:
    keywords = (
        "tarefa",
        "tarefas",
        "lista",
        "pendente",
        "prazo",
        "deadline",
    )
    return any(keyword in message_lower for keyword in keywords)


def _dispatch_tool(name: str, raw_arguments: str) -> Dict[str, Any]:
    try:
        arguments = json.loads(raw_arguments) if raw_arguments else {}
    except json.JSONDecodeError:
        arguments = {}

    try:
        if name == "search_documents":
            query = str(arguments.get("query", ""))
            top_k = int(arguments.get("top_k", 4))
            return search_documents(query=query, top_k=top_k)
        if name == "get_agenda":
            return {"agenda": agenda_as_text()}
        if name == "add_task":
            return create_task(
                title=str(arguments.get("title", "")),
                description=arguments.get("description"),
                due_date=arguments.get("due_date"),
            )
        if name == "list_tasks":
            include_completed = bool(arguments.get("include_completed", True))
            return {"tasks": list_tasks(include_completed=include_completed)}
        if name == "complete_task": # to-do: fazer com que busque por nome da tarefa também
            task_id = int(arguments.get("task_id"))
            completed = bool(arguments.get("completed", True))
            return complete_task(task_id=task_id, completed=completed) or {"error": "Task not found"}
        if name == "update_task":
            task_id = int(arguments.get("task_id"))
            return update_task(
                task_id=task_id,
                title=arguments.get("title"),
                description=arguments.get("description"),
                due_date=arguments.get("due_date"),
                completed=arguments.get("completed"),
            ) or {"error": "Task not found"}
        if name == "delete_task":
            task_id = int(arguments.get("task_id"))
            return {"deleted": delete_task(task_id)}
    except Exception as exc:
        return {"error": str(exc)}

    return {"error": f"Unknown tool: {name}"}
