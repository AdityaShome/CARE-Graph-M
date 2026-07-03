from __future__ import annotations
import re
from care.jury.models import Claim


_UNIT_GROUPS: list[set[str]] = [
    {"km", "kilometer", "kilometres"},
    {"m", "meter", "metres"},
    {"kg", "kilogram", "kilograms"},
    {"usd", "dollar", "dollars", "$"},
    {"eur", "euro", "euros", "€"},
    {"%", "percent", "percentage"},
]


def _same_unit_group(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return True
    al, bl = a.lower(), b.lower()
    if al == bl:
        return True
    for group in _UNIT_GROUPS:
        if al in group and bl in group:
            return True
    return False


def validate_math(claim: Claim, ev_value: float | None, ev_unit: str | None) -> float:
    if claim.claim_type not in ("numeric_fact", "formula"):
        return 0.5
    if claim.value is None or ev_value is None:
        return 0.5
    if not _same_unit_group(claim.unit, ev_unit):
        return 0.1
    delta = abs(claim.value - ev_value) / max(abs(ev_value), 1e-9)
    return max(0.0, 1.0 - delta)
