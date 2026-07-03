from __future__ import annotations
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from care.jury.models import JuryVerdict

_DB_PATH = os.environ.get("CARE_SQLITE_PATH", "care_evidence.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS audit_records (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            question TEXT,
            raw_answer TEXT,
            governed_answer TEXT,
            verdict TEXT,
            confidence REAL,
            confidence_json TEXT,
            sources_json TEXT,
            corrections_json TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS analysis_rounds (
            id TEXT PRIMARY KEY,
            audit_id TEXT,
            round_num INTEGER,
            claim_json TEXT,
            evidence_json TEXT,
            verdict_json TEXT
        )"""
    )
    conn.commit()
    return conn


def log_verdict(question: str, verdict: JuryVerdict) -> str:
    audit_id = str(uuid.uuid4())
    verdict.audit_id = audit_id
    corrections = [
        {"claim": cv.claim.text, "correction": cv.correction}
        for cv in verdict.claim_verdicts
        if cv.correction
    ]
    sources = list(
        {e.source_id for cv in verdict.claim_verdicts for e in cv.evidence_used}
    )
    try:
        conn = _conn()
        conn.execute(
            "INSERT INTO audit_records VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                audit_id,
                datetime.now(timezone.utc).isoformat(),
                question,
                verdict.raw_answer,
                verdict.governed_answer,
                verdict.overall,
                verdict.confidence_scalar,
                json.dumps({}),
                json.dumps(sources),
                json.dumps(corrections),
            ),
        )
        for i, cv in enumerate(verdict.claim_verdicts):
            ev_list = [e.source_id for e in cv.evidence_used]
            conn.execute(
                "INSERT INTO analysis_rounds VALUES (?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    audit_id,
                    i,
                    json.dumps({"text": cv.claim.text, "type": cv.claim.claim_type}),
                    json.dumps(ev_list),
                    json.dumps({"relation": cv.relation, "confidence": cv.confidence.scalar()}),
                ),
            )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return audit_id


def get_record(audit_id: str) -> dict | None:
    try:
        conn = _conn()
        row = conn.execute(
            "SELECT * FROM audit_records WHERE id=?", (audit_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        cols = ["id", "timestamp", "question", "raw_answer", "governed_answer",
                "verdict", "confidence", "confidence_json", "sources_json", "corrections_json"]
        return dict(zip(cols, row))
    except Exception:
        return None


def list_records(limit: int = 20) -> list[dict]:
    try:
        conn = _conn()
        rows = conn.execute(
            "SELECT id, timestamp, question, verdict, confidence FROM audit_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(zip(["id", "timestamp", "question", "verdict", "confidence"], r)) for r in rows]
    except Exception:
        return []
