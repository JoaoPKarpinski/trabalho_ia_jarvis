from __future__ import annotations

import unicodedata
from io import BytesIO
from typing import Dict, List

import pandas as pd

from database.sqlite_manager import list_agenda_entries, insert_agenda_entries


def save_agenda(file_bytes: bytes) -> None:
    df = _csv_bytes_to_dataframe(file_bytes)
    insert_agenda_entries(df)


def agenda_as_text() -> str:
    entries = list_agenda_entries()
    if not entries:
        return "Agenda is empty."

    lines: List[str] = []
    for idx, entry in enumerate(entries, start=1):
        parts = _format_entry_parts(entry)
        if parts:
            lines.append(f"{idx}. " + "; ".join(parts))

    if not lines:
        return "Agenda is empty."

    return "Agenda entries:\n" + "\n".join(lines)

def _csv_bytes_to_dataframe(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(BytesIO(file_bytes), dtype=str)
    df.columns = [_normalize_column_name(col) for col in df.columns]

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.date
    if "hora" in df.columns:
        df["hora"] = pd.to_datetime(df["hora"], errors="coerce").dt.time
    if "observacoes" in df.columns:
        df["observacoes"] = df["observacoes"].str.strip()
    if "titulo" in df.columns:
        df["titulo"] = df["titulo"].str.strip()

    return df.to_dict(orient='records')


def _normalize_column_name(name: object) -> str:
    raw = str(name).strip().lower()
    normalized = unicodedata.normalize("NFKD", raw)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _format_entry_parts(entry: Dict[str, object]) -> List[str]:
    parts: List[str] = []
    for label in ("date", "time", "title", "location", "notes"):
        value = entry.get(label)
        if value:
            parts.append(f"{label}: {value}")

    if parts:
        return parts

    raw = entry.get("raw")
    if isinstance(raw, dict):
        for key, value in raw.items():
            if value:
                parts.append(f"{key}: {value}")
    return parts
