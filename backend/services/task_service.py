from __future__ import annotations

from typing import Any, Dict, List, Optional

from database.sqlite_manager import (
    create_task as create_task_record,
    delete_task as delete_task_record,
    get_task as get_task_record,
    list_tasks as list_task_records,
    update_task as update_task_record,
)


def create_task(title: str, description: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    return create_task_record(title=title, description=description, due_date=due_date)


def list_tasks(include_completed: bool = True) -> List[Dict[str, Any]]:
    return list_task_records(include_completed=include_completed)


def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    return get_task_record(task_id)


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    return update_task_record(
        task_id=task_id,
        title=title,
        description=description,
        due_date=due_date,
        completed=completed,
    )


def complete_task(task_id: int, completed: bool = True) -> Optional[Dict[str, Any]]:
    return update_task_record(task_id=task_id, completed=completed)


def delete_task(task_id: int) -> bool:
    return delete_task_record(task_id)
