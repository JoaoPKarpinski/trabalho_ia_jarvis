from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.sqlite_manager import init_db
from routers import agenda, chat, documents, tasks

app = FastAPI(title="Jarvis Academic Backend")


@app.on_event("startup")
def on_startup() -> None:
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(agenda.router, prefix="/api", tags=["agenda"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])

app.mount("/", StaticFiles(directory="dist", html=True), name="static") # front-end


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
