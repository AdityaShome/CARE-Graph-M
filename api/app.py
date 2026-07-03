from __future__ import annotations
import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from care.service.governed import run_jury
from care.ingestion.text import ingest_text
from care.ingestion.table import ingest_table, ingest_csv
from care.graph.store import get_store
from care.jury.audit_logger import get_record, list_records
from care.research.paper_agent import search_papers, process_paper, decide_paper
from care.research.arxiv_search import PaperCard
from care.jury.models import Claim

log = logging.getLogger("care.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="CARE-Graph-M", version="0.1.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    name = type(exc).__name__
    msg = str(exc)
    # Surface auth errors clearly
    if "auth" in name.lower() or "401" in msg or "api key" in msg.lower() or "invalid_api_key" in msg.lower():
        log.error("LLM auth error: %s", msg)
        return JSONResponse(status_code=401, content={"detail": f"LLM authentication failed — check your API key. ({name})"})
    log.exception("Unhandled error in %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"{name}: {msg}"})


UI_DIR = Path(__file__).parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

_MAX_QUESTION   = 2000
_MAX_EV_SOURCES = 20
_MAX_EV_CONTENT = 50_000   # chars per source


# ── Request models ─────────────────────────────────────────────────────────────

class IngestTextRequest(BaseModel):
    source_id: str
    text: str
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        if len(v) > _MAX_EV_CONTENT:
            raise ValueError(f"text exceeds {_MAX_EV_CONTENT} characters")
        return v


class IngestTableRequest(BaseModel):
    source_id: str
    path: str | None = None
    rows: list[dict[str, Any]] | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    query: str
    budget: int = 512

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query must not be empty")
        if len(v) > _MAX_QUESTION:
            raise ValueError(f"query exceeds {_MAX_QUESTION} characters")
        return v


class VerifyGenerateRequest(BaseModel):
    """Real governed-answer endpoint. No fault injection."""
    question: str
    use_graph_context: bool = False
    evidence_sources: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        if len(v) > _MAX_QUESTION:
            raise ValueError(f"question exceeds {_MAX_QUESTION} characters")
        return v

    @field_validator("evidence_sources")
    @classmethod
    def evidence_within_limits(cls, v: list) -> list:
        if len(v) > _MAX_EV_SOURCES:
            raise ValueError(f"evidence_sources exceeds {_MAX_EV_SOURCES} items")
        return v


class DemoGenerateRequest(BaseModel):
    """Demo endpoint — explicitly supports fault injection for demonstrations."""
    question: str
    fault_inject: bool = False
    use_graph_context: bool = False
    evidence_sources: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        if len(v) > _MAX_QUESTION:
            raise ValueError(f"question exceeds {_MAX_QUESTION} characters")
        return v


class PaperSearchRequest(BaseModel):
    topic: str
    use_demo_fallback: bool = True


class PaperProcessRequest(BaseModel):
    paper_id: str
    title: str
    pdf_url: str
    abs_url: str = ""
    claims: list[str] = Field(default_factory=list)


class PaperDecideRequest(BaseModel):
    paper_id: str
    title: str
    decision: str
    overall_accuracy: float = 0.0
    claim_results: list[dict] = Field(default_factory=list)


# ── Shared response helper ─────────────────────────────────────────────────────

def _verdict_response(verdict) -> dict:
    claim_details = []
    for cv in verdict.claim_verdicts:
        claim_details.append({
            "claim": cv.claim.text,
            "claim_type": cv.claim.claim_type,
            "relation": cv.relation,
            "correction": cv.correction,
            "confidence": cv.confidence.to_dict(),
            "evidence": [
                {"source_id": e.source_id, "content": e.content[:300]}
                for e in cv.evidence_used
            ],
        })
    return {
        "raw_answer": verdict.raw_answer,
        "governed_answer": verdict.governed_answer,
        "verdict": verdict.overall,
        "confidence": verdict.confidence_scalar,
        "claims": claim_details,
        "audit_id": verdict.audit_id,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    provider = os.environ.get("CARE_LLM_PROVIDER", "mock")
    backend  = os.environ.get("CARE_GRAPH_BACKEND", "memory")
    store_size = len(get_store().all())
    return {"status": "ok", "llm_provider": provider, "graph_backend": backend, "evidence_count": store_size}


@app.get("/")
def root():
    return RedirectResponse(url="/ui/index.html")


@app.post("/ingest/text")
async def ingest_text_route(req: IngestTextRequest):
    store = get_store()
    objects = await asyncio.to_thread(ingest_text, req.source_id, req.text, req.source_metadata)
    store.add(objects)
    log.info("ingested text source_id=%s chunks=%d", req.source_id, len(objects))
    return {"ingested": len(objects), "source_id": req.source_id}


@app.post("/ingest/table")
async def ingest_table_route(req: IngestTableRequest):
    store = get_store()
    if req.path:
        objects = await asyncio.to_thread(ingest_csv, req.source_id, req.path, req.source_metadata)
    elif req.rows:
        objects = await asyncio.to_thread(ingest_table, req.source_id, req.rows, req.source_metadata)
    else:
        raise HTTPException(400, "Provide either 'path' or 'rows'")
    store.add(objects)
    log.info("ingested table source_id=%s rows=%d", req.source_id, len(objects))
    return {"ingested": len(objects), "source_id": req.source_id}


@app.post("/ingest/pdf")
async def ingest_pdf_route(source_id: str, file: UploadFile = File(...)):
    from care.ingestion.pdf import ingest_pdf
    store = get_store()
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        objects = await asyncio.to_thread(ingest_pdf, source_id, tmp_path, {"source_type": "research_paper"})
        store.add(objects)
        log.info("ingested pdf source_id=%s pages=%d", source_id, len(objects))
        return {"ingested": len(objects), "source_id": source_id}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/query")
async def query_route(req: QueryRequest):
    def _run():
        return run_jury(question=req.query, use_graph_context=True)

    verdict = await asyncio.to_thread(_run)
    primary, supporting, contradictions = [], [], []
    for cv in verdict.claim_verdicts:
        for ev in cv.evidence_used:
            entry = {"source_id": ev.source_id, "content": ev.content[:200], "source_type": ev.source_type}
            if cv.relation == "supported":
                primary.append(entry)
            elif cv.relation == "contradicted":
                contradictions.append(entry)
            else:
                supporting.append(entry)
    return {
        "answer": verdict.governed_answer,
        "evidence": {
            "primary": primary[:3],
            "supporting": supporting[:3],
            "contradictions": contradictions[:3],
        },
        "summary": f"Verdict: {verdict.overall}. Confidence: {verdict.confidence_scalar:.2f}",
        "verdict": verdict.overall,
        "confidence": verdict.confidence_scalar,
        "audit_id": verdict.audit_id,
    }


@app.post("/verify/generate")
async def verify_generate_route(req: VerifyGenerateRequest):
    """Governed answer pipeline. No fault injection."""
    def _run():
        return run_jury(
            question=req.question,
            evidence_sources=req.evidence_sources,
            use_graph_context=req.use_graph_context,
            fault_inject=False,
        )
    verdict = await asyncio.to_thread(_run)
    log.info("verify/generate verdict=%s confidence=%.2f", verdict.overall, verdict.confidence_scalar)
    return _verdict_response(verdict)


@app.post("/demo/generate")
async def demo_generate_route(req: DemoGenerateRequest):
    """Demo pipeline. Supports fault_inject for demonstration purposes."""
    def _run():
        return run_jury(
            question=req.question,
            evidence_sources=req.evidence_sources,
            use_graph_context=req.use_graph_context,
            fault_inject=req.fault_inject,
        )
    verdict = await asyncio.to_thread(_run)
    log.info("demo/generate fault=%s verdict=%s", req.fault_inject, verdict.overall)
    return _verdict_response(verdict)


@app.get("/audit/{audit_id}")
def get_audit(audit_id: str):
    record = get_record(audit_id)
    if record is None:
        raise HTTPException(404, "Audit record not found")
    return record


@app.get("/audit")
def list_audits(limit: int = Query(default=20, le=100)):
    return {"records": list_records(limit)}


@app.get("/store")
def store_contents():
    """Return a summary of all evidence currently in the in-memory store."""
    objects = get_store().all()
    return {
        "count": len(objects),
        "sources": [
            {
                "source_id": o.source_id,
                "source_type": o.source_type,
                "content_preview": o.content[:120],
                "reliability": o.reliability_score,
            }
            for o in objects
        ],
    }


@app.delete("/store")
def clear_store():
    get_store().clear()
    return {"status": "cleared"}


@app.post("/papers/search")
async def papers_search(req: PaperSearchRequest):
    cards = await asyncio.to_thread(search_papers, req.topic, req.use_demo_fallback)
    return {
        "topic": req.topic,
        "papers": [
            {
                "paper_id": c.paper_id,
                "title": c.title,
                "authors": c.authors,
                "summary": c.summary,
                "abs_url": c.abs_url,
                "pdf_url": c.pdf_url,
                "published": c.published,
            }
            for c in cards
        ],
    }


@app.post("/papers/process")
async def papers_process(req: PaperProcessRequest):
    card = PaperCard(
        paper_id=req.paper_id, title=req.title, authors=[],
        summary="", abs_url=req.abs_url, pdf_url=req.pdf_url, published="",
    )
    claims = [Claim(text=t, claim_type="generic") for t in req.claims] if req.claims else None
    result = await asyncio.to_thread(process_paper, card, claims)
    if result is None:
        raise HTTPException(500, "Paper processing failed")
    return {
        "paper_id": result.paper_id,
        "title": result.title,
        "overall_accuracy": result.overall_accuracy,
        "claim_results": [
            {"claim": r.claim_text, "verdict": r.verdict, "reason": r.reason, "accuracy": r.accuracy}
            for r in result.claim_results
        ],
    }


@app.post("/papers/decide")
def papers_decide(req: PaperDecideRequest):
    if req.decision not in ("approve", "stall", "reject"):
        raise HTTPException(400, "decision must be approve, stall, or reject")
    from care.research.paper_verifier import PaperVerdictResult, PaperClaimResult
    result = PaperVerdictResult(
        paper_id=req.paper_id,
        title=req.title,
        overall_accuracy=req.overall_accuracy,
        claim_results=[
            PaperClaimResult(
                claim_text=r.get("claim", ""), verdict=r.get("verdict", ""),
                reason=r.get("reason", ""), accuracy=r.get("accuracy", 0.0),
            )
            for r in req.claim_results
        ],
    )
    card = PaperCard(paper_id=req.paper_id, title=req.title, authors=[], summary="", abs_url="", pdf_url="", published="")
    decide_paper(result, req.decision, card)
    return {"status": "ok", "decision": req.decision, "paper_id": req.paper_id}
