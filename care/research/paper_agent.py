from __future__ import annotations
import json
import os
from dataclasses import asdict, dataclass, field
from care.research.arxiv_search import PaperCard, search_arxiv
from care.research.paper_parser import download_and_parse
from care.research.paper_evidence import extract_paper_evidence, PaperEvidenceGraph
from care.research.paper_verifier import verify_against_paper, PaperVerdictResult
from care.research.demo_papers import demo_paper_cards, build_demo_evidence_graph
from care.jury.models import Claim

_APPROVED_PATH = "approved_paper_evidence.json"
_STALLED_PATH = "stalled_paper_archive.json"
_REJECTED_PATH = "rejected_paper_signals.json"


def _load_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def _append_json(path: str, record: dict) -> None:
    records = _load_json(path)
    records.append(record)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)


def search_papers(topic: str, use_demo_fallback: bool = True) -> list[PaperCard]:
    cards = search_arxiv(topic, max_results=8)
    if not cards and use_demo_fallback:
        cards = demo_paper_cards(topic)
    return cards


def process_paper(card: PaperCard, claims: list[Claim] | None = None) -> PaperVerdictResult | None:
    is_demo = card.paper_id.startswith("demo-")

    if is_demo:
        graph = build_demo_evidence_graph(card.paper_id)
    else:
        parsed = download_and_parse(card.paper_id, card.title, card.pdf_url)
        if parsed is None:
            # Fall back to demo
            graph = build_demo_evidence_graph(card.paper_id)
        else:
            graph = extract_paper_evidence(parsed)

    if graph is None:
        return None

    if not claims:
        from care.jury.models import Claim as C
        claims = [C(text=card.summary[:200], claim_type="generic")]

    return verify_against_paper(claims, graph)


def decide_paper(
    result: PaperVerdictResult,
    decision: str,
    card: PaperCard,
) -> None:
    record = {
        "paper_id": result.paper_id,
        "title": result.title,
        "decision": decision,
        "overall_accuracy": result.overall_accuracy,
        "claim_results": [
            {"claim": r.claim_text, "verdict": r.verdict, "reason": r.reason, "accuracy": r.accuracy}
            for r in result.claim_results
        ],
    }
    if decision == "approve":
        _append_json(_APPROVED_PATH, record)
    elif decision == "stall":
        _append_json(_STALLED_PATH, record)
    else:
        _append_json(_REJECTED_PATH, record)
