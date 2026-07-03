from __future__ import annotations
from care.research.arxiv_search import PaperCard
from care.research.paper_parser import ParsedPaper
from care.research.paper_evidence import PaperEvidenceGraph

_DEMO_PAPERS: list[dict] = [
    {
        "paper_id": "demo-hallucination-2024",
        "title": "Hallucination Detection in Large Language Models via Claim Decomposition",
        "summary": "We propose a claim-decomposition pipeline that intercepts LLM outputs and verifies each atomic fact against a curated knowledge base, reducing hallucination rate by 38% on TruthfulQA.",
        "topic_keywords": ["hallucination", "hallucination detection", "factuality", "fact verification"],
        "results": [
            {"value": 38.0, "unit": "%", "context": "Reduces hallucination rate by 38% on TruthfulQA"},
            {"value": 0.84, "unit": "F1", "context": "F1 score of 0.84 on HaluEval benchmark"},
        ],
        "conclusions": [
            "Claim decomposition significantly reduces hallucination rate compared to end-to-end verification.",
            "The pipeline generalizes across three domains: medical, legal, and scientific.",
        ],
        "limitations": [
            "Evaluation limited to English-language benchmarks.",
            "Performance may degrade on highly specialized domains.",
        ],
    },
    {
        "paper_id": "demo-rag-2024",
        "title": "Retrieval-Augmented Classification with Evidence Grounding",
        "summary": "A retrieval-augmented approach for multi-label classification that improves F1 score on three English low-resource datasets by 12 points by grounding predictions in retrieved evidence.",
        "topic_keywords": ["retrieval", "rag", "retrieval augmented", "classification"],
        "results": [
            {"value": 12.0, "unit": "points", "context": "F1 improvement of 12 points on low-resource datasets"},
            {"value": 0.76, "unit": "F1", "context": "Average F1 of 0.76 across three datasets"},
        ],
        "conclusions": [
            "The model improves F1 score on three English low-resource datasets.",
            "Evidence grounding reduces false positive rate by 22%.",
        ],
        "limitations": [
            "Evaluated only on English datasets.",
            "Retrieval quality depends on index freshness.",
        ],
    },
    {
        "paper_id": "demo-medical-2024",
        "title": "Faithful Medical Summarization with Contradiction Detection",
        "summary": "We introduce a medical summarization system that detects contradictions between generated summaries and source clinical notes, achieving 91% faithfulness on MIMIC-III discharge summaries.",
        "topic_keywords": ["medical", "summarization", "clinical", "healthcare"],
        "results": [
            {"value": 91.0, "unit": "%", "context": "91% faithfulness on MIMIC-III discharge summaries"},
        ],
        "conclusions": [
            "Contradiction detection improves faithfulness by 18% over baseline summarization.",
            "The system flags 94% of clinically significant errors.",
        ],
        "limitations": [
            "Dataset limited to MIMIC-III; not validated on non-English records.",
        ],
    },
    {
        "paper_id": "demo-structural-2024",
        "title": "AI-Assisted Structural Engineering Verification",
        "summary": "An AI pipeline for verifying structural engineering calculations, cross-referencing LLM outputs with building codes and FEM simulations.",
        "topic_keywords": ["structural", "engineering", "verification", "calculation"],
        "results": [
            {"value": 97.0, "unit": "%", "context": "97% agreement with expert review on load calculations"},
        ],
        "conclusions": [
            "The pipeline catches 89% of numerical errors in beam load calculations.",
        ],
        "limitations": [
            "Only evaluated on standard steel frame structures.",
        ],
    },
    {
        "paper_id": "demo-quantum-2024",
        "title": "Quantum Error Correction with LLM-Assisted Syndrome Decoding",
        "summary": "We explore using language models to assist syndrome decoding for surface codes, achieving a logical error rate of 0.3% under depolarizing noise.",
        "topic_keywords": ["quantum", "error correction", "syndrome", "qec"],
        "results": [
            {"value": 0.3, "unit": "%", "context": "Logical error rate of 0.3% under depolarizing noise"},
        ],
        "conclusions": [
            "LLM-assisted decoding matches threshold performance of classical MWPM decoders.",
        ],
        "limitations": [
            "Only tested on surface codes up to distance 7.",
        ],
    },
    {
        "paper_id": "demo-multimodal-2024",
        "title": "Multimodal Hallucination Detection via Cross-Modal Grounding",
        "summary": "A cross-modal approach to detecting hallucinations in image-captioning systems by grounding textual claims against visual features.",
        "topic_keywords": ["multimodal", "image", "vision", "captioning", "visual"],
        "results": [
            {"value": 0.88, "unit": "AUC", "context": "AUC of 0.88 on CHAIR benchmark"},
        ],
        "conclusions": [
            "Cross-modal grounding reduces CHAIR score by 31% compared to text-only verification.",
        ],
        "limitations": [
            "Requires aligned vision encoder; not tested on video.",
        ],
    },
    {
        "paper_id": "demo-multiagent-2024",
        "title": "Multi-Agent Verification for Governed AI Pipelines",
        "summary": "A five-agent jury architecture for AI output governance, demonstrating 94% verdict accuracy on a curated hallucination benchmark.",
        "topic_keywords": ["multi-agent", "agent", "verification", "governance", "jury", "governed"],
        "results": [
            {"value": 94.0, "unit": "%", "context": "94% verdict accuracy on hallucination benchmark"},
        ],
        "conclusions": [
            "Multi-agent verification outperforms single-model self-consistency by 17%.",
            "Audit trail increases user trust by 40% in user studies.",
        ],
        "limitations": [
            "Latency increases by 3x compared to single-model generation.",
        ],
    },
]

_TOPIC_MAP: dict[str, dict] = {}
for _p in _DEMO_PAPERS:
    for _kw in _p["topic_keywords"]:
        _TOPIC_MAP[_kw] = _p


def get_demo_paper(topic: str) -> dict | None:
    low = topic.lower()
    for kw, paper in _TOPIC_MAP.items():
        if kw in low:
            return paper
    return None


def demo_paper_cards(topic: str) -> list[PaperCard]:
    paper = get_demo_paper(topic)
    candidates = [paper] if paper else _DEMO_PAPERS[:3]
    cards: list[PaperCard] = []
    for p in candidates:
        cards.append(
            PaperCard(
                paper_id=p["paper_id"],
                title=f"[Synthetic demo paper] {p['title']}",
                authors=["Demo Author et al."],
                summary=p["summary"],
                abs_url=f"https://arxiv.org/abs/{p['paper_id']}",
                pdf_url=f"https://arxiv.org/pdf/{p['paper_id']}.pdf",
                published="2024-01-01T00:00:00Z",
            )
        )
    return cards


def build_demo_evidence_graph(paper_id: str) -> PaperEvidenceGraph | None:
    paper = next((p for p in _DEMO_PAPERS if p["paper_id"] == paper_id), None)
    if paper is None:
        return None
    g = PaperEvidenceGraph(paper_id=paper_id, title=paper["title"])
    g.research_problem = paper["summary"]
    g.proposed_method = paper["summary"]
    g.numerical_results = paper.get("results", [])
    g.conclusions = paper.get("conclusions", [])
    g.limitations = paper.get("limitations", [])
    return g
