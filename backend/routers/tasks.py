from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.task_service import complete_task, create_task, delete_task, list_tasks, update_task

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None


@router.get("/tasks")
def get_tasks(include_completed: bool = Query(True)) -> Dict[str, List[Dict[str, Any]]]:
    return {"tasks": list_tasks(include_completed=include_completed)}


@router.post("/tasks")
def create_task_endpoint(payload: TaskCreate) -> Dict[str, Any]:
    return create_task(title=payload.title, description=payload.description, due_date=payload.due_date)


@router.patch("/tasks/{task_id}")
def update_task_endpoint(task_id: int, payload: TaskUpdate) -> Dict[str, Any]:
    updated = update_task(
        task_id=task_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        completed=payload.completed,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.put("/tasks/{task_id}/complete")
def complete_task_endpoint(task_id: int) -> Dict[str, Any]:
    updated = complete_task(task_id=task_id, completed=True)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/tasks/{task_id}")
def delete_task_endpoint(task_id: int) -> Dict[str, Any]:
    deleted = delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}
