from __future__ import annotations
import io
import re
import urllib.request
from dataclasses import dataclass, field

_HEADING_RE = re.compile(
    r"^\s*(?:\d+\.?\s+)?([A-Z][A-Za-z\s]{2,40})\s*$", re.MULTILINE
)
_KNOWN_SECTIONS = {
    "abstract", "introduction", "related work", "background",
    "method", "methodology", "approach", "model",
    "experiments", "results", "evaluation", "discussion",
    "conclusion", "limitations", "acknowledgements", "references",
}


@dataclass
class ParsedPaper:
    paper_id: str
    title: str
    full_text: str
    sections: dict[str, str] = field(default_factory=dict)


def _extract_sections(text: str) -> dict[str, str]:
    lines = text.split("\n")
    sections: dict[str, str] = {}
    current = "preamble"
    buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        is_heading = bool(_HEADING_RE.match(line)) and len(stripped) < 60
        is_known = any(kw in stripped.lower() for kw in _KNOWN_SECTIONS)
        if is_heading and is_known:
            sections[current] = "\n".join(buf).strip()
            current = stripped.lower()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf).strip()
    return {k: v for k, v in sections.items() if v}


def parse_pdf_bytes(paper_id: str, title: str, data: bytes) -> ParsedPaper:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        full_text = "\n".join(pages)
    except Exception:
        full_text = data.decode("utf-8", errors="ignore")
    sections = _extract_sections(full_text)
    return ParsedPaper(paper_id=paper_id, title=title, full_text=full_text, sections=sections)


def download_and_parse(paper_id: str, title: str, pdf_url: str) -> ParsedPaper | None:
    try:
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "CARE-Graph-M/0.1"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        return parse_pdf_bytes(paper_id, title, data)
    except Exception:
        return None
