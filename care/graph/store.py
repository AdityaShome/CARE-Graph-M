from __future__ import annotations
import json
import os
import sqlite3
from care.jury.models import EvidenceObject

_DB_PATH = os.environ.get("CARE_SQLITE_PATH", "care_evidence.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            source_id TEXT,
            source_type TEXT,
            content TEXT,
            metadata TEXT,
            reliability_score REAL
        )"""
    )
    conn.commit()
    return conn


class EvidenceStore:
    def __init__(self) -> None:
        self._mem: dict[str, EvidenceObject] = {}

    def add(self, objects: list[EvidenceObject]) -> None:
        for obj in objects:
            self._mem[obj.source_id] = obj
        try:
            conn = _get_conn()
            conn.executemany(
                "INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?)",
                [
                    (
                        o.source_id,
                        o.source_id.split("::")[0],
                        o.source_type,
                        o.content,
                        json.dumps(o.metadata),
                        o.reliability_score,
                    )
                    for o in objects
                ],
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def search(self, query: str, top_k: int = 5) -> list[EvidenceObject]:
        query_words = set(query.lower().split())
        scored: list[tuple[float, EvidenceObject]] = []
        for obj in self._mem.values():
            content_words = set(obj.content.lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored.append((overlap / len(query_words | content_words), obj))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [obj for _, obj in scored[:top_k]]

    def all(self) -> list[EvidenceObject]:
        return list(self._mem.values())

    def clear(self) -> None:
        self._mem.clear()


_global_store = EvidenceStore()


def get_store() -> EvidenceStore:
    return _global_store
