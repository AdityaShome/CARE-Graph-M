from __future__ import annotations
import re
from dataclasses import dataclass, field
from care.research.paper_parser import ParsedPaper

_NUM_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(%|points?|pp\.?|F1|BLEU|ROUGE|accuracy|score)?\b")


@dataclass
class PaperEvidenceGraph:
    paper_id: str
    title: str
    research_problem: str = ""
    proposed_method: str = ""
    techniques: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    numerical_results: list[dict] = field(default_factory=list)
    baselines: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)
    weak_claims: list[str] = field(default_factory=list)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]


def _grep(text: str, keywords: list[str]) -> list[str]:
    sents = _sentences(text)
    return [s for s in sents if any(kw.lower() in s.lower() for kw in keywords)]


def extract_paper_evidence(paper: ParsedPaper) -> PaperEvidenceGraph:
    g = PaperEvidenceGraph(paper_id=paper.paper_id, title=paper.title)
    abstract = paper.sections.get("abstract", paper.full_text[:800])
    intro = paper.sections.get("introduction", "")
    method = paper.sections.get("method", paper.sections.get("methodology", paper.sections.get("approach", "")))
    results = paper.sections.get("results", paper.sections.get("experiments", paper.sections.get("evaluation", "")))
    conclusion = paper.sections.get("conclusion", "")
    limitations_sec = paper.sections.get("limitations", "")

    g.research_problem = abstract[:300] if abstract else ""
    g.proposed_method = method[:300] if method else intro[:300]

    g.techniques = _grep(method or intro, ["attention", "transformer", "encoder", "decoder", "graph", "neural", "bert", "gpt"])[:5]
    g.datasets = _grep(results or paper.full_text, ["dataset", "benchmark", "corpus", "split", "training set"])[:5]
    g.baselines = _grep(results or paper.full_text, ["baseline", "compared", "vs.", "versus", "prior"])[:5]
    g.metrics = _grep(results or paper.full_text, ["F1", "accuracy", "BLEU", "ROUGE", "precision", "recall", "AUC"])[:5]
    g.limitations = _sentences(limitations_sec)[:5] if limitations_sec else _grep(paper.full_text, ["limitation", "does not", "cannot", "future work"])[:3]
    g.conclusions = _sentences(conclusion)[:5] if conclusion else []
    g.weak_claims = _grep(paper.full_text, ["may", "might", "could potentially", "we believe", "we conjecture"])[:5]

    for match in _NUM_RE.finditer(results or paper.full_text):
        g.numerical_results.append({
            "value": float(match.group(1)),
            "unit": match.group(2) or "",
            "context": paper.full_text[max(0, match.start()-60):match.end()+60].strip(),
        })
        if len(g.numerical_results) >= 10:
            break

    return g
