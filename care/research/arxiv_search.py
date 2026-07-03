from __future__ import annotations
import urllib.parse
import urllib.request
from dataclasses import dataclass
import feedparser


@dataclass
class PaperCard:
    paper_id: str
    title: str
    authors: list[str]
    summary: str
    abs_url: str
    pdf_url: str
    published: str


def search_arxiv(query: str, max_results: int = 8) -> list[PaperCard]:
    encoded = urllib.parse.quote(query)
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query=all:{encoded}&start=0&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            content = resp.read().decode("utf-8")
        feed = feedparser.parse(content)
    except Exception:
        return []

    cards: list[PaperCard] = []
    for entry in feed.entries:
        abs_url = entry.get("link", "")
        pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"
        paper_id = abs_url.split("/abs/")[-1] if "/abs/" in abs_url else abs_url
        authors = [a.get("name", "") for a in entry.get("authors", [])]
        cards.append(
            PaperCard(
                paper_id=paper_id,
                title=entry.get("title", "").replace("\n", " ").strip(),
                authors=authors,
                summary=entry.get("summary", "").replace("\n", " ").strip(),
                abs_url=abs_url,
                pdf_url=pdf_url,
                published=entry.get("published", ""),
            )
        )
    return cards
