from __future__ import annotations
from care.jury.models import EvidenceObject
from care.graph.store import EvidenceStore


def retrieve(
    query: str,
    store: EvidenceStore,
    top_k: int = 5,
) -> list[EvidenceObject]:
    return store.search(query, top_k=top_k)
