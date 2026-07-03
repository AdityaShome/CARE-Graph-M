from __future__ import annotations
import re
from dataclasses import dataclass, field
from care.jury.models import Claim
from care.research.paper_evidence import PaperEvidenceGraph

_OVERGEN_PHRASES = [
    "all languages", "all domains", "always", "universally",
    "in every", "across all", "for all tasks",
]


@dataclass
class PaperClaimResult:
    claim_text: str
    verdict: str
    reason: str
    accuracy: float = 0.0


@dataclass
class PaperVerdictResult:
    paper_id: str
    title: str
    claim_results: list[PaperClaimResult] = field(default_factory=list)
    overall_accuracy: float = 0.0


def _overgeneralizes(claim_text: str) -> bool:
    low = claim_text.lower()
    return any(phrase in low for phrase in _OVERGEN_PHRASES)


def _numeric_in_paper(value: float, graph: PaperEvidenceGraph, tolerance: float = 0.05) -> bool:
    for r in graph.numerical_results:
        if abs(r["value"] - value) / max(abs(r["value"]), 1e-9) <= tolerance:
            return True
    return False


def verify_against_paper(
    claims: list[Claim],
    graph: PaperEvidenceGraph,
) -> PaperVerdictResult:
    results: list[PaperClaimResult] = []
    full_text_lower = (
        graph.research_problem + graph.proposed_method +
        " ".join(graph.conclusions) + " ".join(graph.limitations)
    ).lower()

    for claim in claims:
        if _overgeneralizes(claim.text):
            scope = next(
                (c for c in graph.conclusions + graph.limitations if c), ""
            )
            results.append(PaperClaimResult(
                claim_text=claim.text,
                verdict="FLAGGED",
                reason=f"Overgeneralization. Paper scope: {scope[:150]}",
                accuracy=0.2,
            ))
            continue

        if claim.value is not None:
            found = _numeric_in_paper(claim.value, graph)
            if found:
                results.append(PaperClaimResult(claim.text, "SUPPORTED", "Numeric value found in paper", 0.9))
            else:
                results.append(PaperClaimResult(claim.text, "UNVERIFIED", "Numeric value not found in paper results", 0.4))
            continue

        keywords = claim.text.lower().split()
        overlap = sum(1 for w in keywords if w in full_text_lower) / max(len(keywords), 1)
        if overlap >= 0.5:
            results.append(PaperClaimResult(claim.text, "SUPPORTED", f"Term overlap: {overlap:.0%}", overlap))
        elif overlap >= 0.2:
            results.append(PaperClaimResult(claim.text, "PARTIALLY_SUPPORTED", f"Partial overlap: {overlap:.0%}", overlap))
        else:
            results.append(PaperClaimResult(claim.text, "UNSUPPORTED", "Low term overlap with paper", overlap))

    overall = sum(r.accuracy for r in results) / max(len(results), 1)
    return PaperVerdictResult(
        paper_id=graph.paper_id,
        title=graph.title,
        claim_results=results,
        overall_accuracy=overall,
    )
