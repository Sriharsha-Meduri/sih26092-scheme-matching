"""INR value normalization.

Transforms Indian financial string notations ("Rs 5 lakh", "₹3.5L", "5,00,000",
"40 lacs", "1 cr", "500000") into a canonical numeric INR value. Trusted
numeric inputs pass through unchanged. Returns None for empty/None so callers
can keep UNKNOWN semantics. Never rounds away detail: converts exactly.
"""

from __future__ import annotations

import math
import re
from typing import Optional, Union

Number = Union[int, float]

_LAKH = 100_000
_CRORE = 10_000_000

_CROWN = re.compile(r"\bCRORE\b|\bCR\b")
_LAKHS = re.compile(r"\bLAKHS?\b|\bLACS?\b|\bLAC\b|L$")


def parse_inr(value: Optional[Union[Number, str]]) -> Optional[Number]:
    """Parse a financial value into a canonical numeric INR (float). None in -> None out."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError("financial value cannot be a boolean")
    if isinstance(value, (int, float)):
        _validate_amount(float(value))
        return float(value)

    raw = str(value).strip()
    if not raw:
        return None

    text = raw.upper()

    multiplier = 1.0
    match = _CROWN.search(text)
    if match:
        multiplier = _CRORE
        text = text[: match.start()] + text[match.end():]
    else:
        match = _LAKHS.search(text)
        if match:
            multiplier = _LAKH
            text = text[: match.start()] + text[match.end():]

    # drop rupee symbol + "Rs" prefix, then separator commas / spaces.
    text = re.sub(r"[₹]", "", text)
    text = re.sub(r"\bRS\b", "", text)
    text = re.sub(r"[, \t]+", "", text)

    if not text:
        raise ValueError(f"unparseable financial value: {value!r}")
    try:
        amount = float(text) * multiplier
    except ValueError as exc:
        raise ValueError(f"unparseable financial value: {value!r}") from exc
    _validate_amount(amount)
    return amount


def _validate_amount(amount: float) -> None:
    if not math.isfinite(amount):
        raise ValueError(f"financial value must be a finite number, got {amount}")
    if amount < 0:
        raise ValueError(f"financial value must be non-negative, got {amount}")
    if amount > 10 ** 12:
        raise ValueError(f"financial value out of plausible range: {amount}")


def format_inr(value: Optional[Number]) -> Optional[str]:
    """Display-only Indian grouping (used in formula details)."""
    if value is None:
        return None
    return f"{float(value):,.2f}"