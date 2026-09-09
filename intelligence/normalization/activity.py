"""Activity normalization (M2 §4, §7).

Resolves raw user activity text ("tailoring shop", "Stitching Unit") to a
canonical M1 activity record when the taxonomy supports it. Matching is
case/whitespace-insensitive and alias-aware (aliases are empty today). When no
canonical activity exists the raw text is preserved and resolution reports
UNKNOWN: we never invent taxonomy entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from intelligence.kb.repository import KnowledgeBase


@dataclass
class ActivityResolution:
    raw: Optional[str]
    resolved: bool = False
    canonical_activity_id: Optional[str] = None
    canonical_activity_name: Optional[str] = None
    sector_ids: list[str] = field(default_factory=list)
    mapping_sources: list[str] = field(default_factory=list)
    mapping_status: Optional[str] = None          # "UNVERIFIED" (all current)
    notes: Optional[str] = None


def resolve_activity(raw: Optional[str], kb: KnowledgeBase) -> ActivityResolution:
    if raw is None or not str(raw).strip():
        return ActivityResolution(raw=raw)
    text = raw.strip()
    record = kb.resolve_activity_name(text)
    if record is None:
        return ActivityResolution(raw=text)
    mapping = kb.activity_mapping(record["id"])
    return ActivityResolution(
        raw=text,
        resolved=True,
        canonical_activity_id=record["id"],
        canonical_activity_name=record["name"],
        sector_ids=list(record.get("sector_ids") or []),
        mapping_sources=list(mapping.get("evidence") or []) if mapping else [],
        mapping_status=(mapping or {}).get("status"),
        notes=(mapping or {}).get("notes"),
    )