from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "database.sqlite"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agenda_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                title TEXT,
                location TEXT,
                notes TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "completed": bool(row["completed"]),
    }


def create_task(title: str, description: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    conn = _connect()
    try:
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, due_date, created_at, completed)
            VALUES (?, ?, ?, ?, 0)
            """,
            (title, description, due_date, created_at),
        )
        conn.commit()
        task_id = cursor.lastrowid
    finally:
        conn.close()
    task = get_task(task_id)
    if not task:
        raise RuntimeError("Failed to create task.")
    return task


def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return _row_to_dict(row)


def list_tasks(include_completed: bool = True) -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        query = "SELECT * FROM tasks"
        params: List[Any] = []
        if not include_completed:
            query += " WHERE completed = 0"
        query += " ORDER BY completed ASC, due_date IS NULL, due_date ASC, id ASC"
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(row) for row in rows]


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    existing = get_task(task_id)
    if not existing:
        return None

    updates: List[str] = []
    params: Dict[str, Any] = {"id": task_id}

    if title is not None:
        updates.append("title = :title")
        params["title"] = title
    if description is not None:
        updates.append("description = :description")
        params["description"] = description
    if due_date is not None:
        updates.append("due_date = :due_date")
        params["due_date"] = due_date
    if completed is not None:
        updates.append("completed = :completed")
        params["completed"] = 1 if completed else 0

    if not updates:
        return existing

    conn = _connect()
    try:
        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = :id", params)
        conn.commit()
    finally:
        conn.close()

    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    conn = _connect()
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def insert_agenda_entries(entries: List[Dict[str, Any]]) -> None:
    conn = _connect()
    try:
        # conn.execute("DELETE FROM agenda_entries") mudado para append, e não replace
        for entry in entries:
            conn.execute(
                """
                INSERT INTO agenda_entries (
                    date,
                    time,
                    title,
                    location,
                    notes
                )
                VALUES ( ?, ?, ?, ?, ?)
                """,
                (
                    str(entry.get("data")),
                    str(entry.get("hora")),
                    str(entry.get("nome")),
                    str(entry.get("local")),
                    str(entry.get("observacoes")),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def list_agenda_entries() -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, date, time, title, location, notes
            FROM agenda_entries
            ORDER BY date DESC, id ASC
            """
        ).fetchall()
    finally:
        conn.close()

    entries: List[Dict[str, Any]] = []
    for row in rows:
        entries.append(
            {
                "id": row["id"],
                "date": row["date"],
                "time": row["time"],
                "title": row["title"],
                "location": row["location"],
                "notes": row["notes"],
            }
        )

    return entries
