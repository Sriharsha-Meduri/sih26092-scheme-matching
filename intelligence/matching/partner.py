"""Partner-availability fit (M2 §7).

M1 partner master is NOT_INGESTED (partners.json stub). Per the hard
constraint, no partner score/figure is fabricated: every scheme's partner
factor is UNAVAILABLE with score 0 and reason PARTNER_DATA_UNAVAILABLE. The
architecture supports real partner data later; only the adapter changes.

Partner sources referenced by the KB gap are listed so the UI can explain why
the dimension is unavailable.
"""

from __future__ import annotations

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import PartnerStatus, Verdict
from intelligence.models.result import PartnerFitResult
from intelligence.explanations import reason_keys as RK


def partner_fit(kb: KnowledgeBase, scheme_id: str) -> PartnerFitResult:
    gap_refs = _partner_gap_source_ids(kb)
    return PartnerFitResult(
        scheme_id=scheme_id,
        status=Verdict.UNKNOWN,
        partner_status=PartnerStatus.UNAVAILABLE,
        score=0,
        reason_key=RK.PARTNER_DATA_UNAVAILABLE,
        sources=gap_refs,
    )


def _partner_gap_source_ids(kb: KnowledgeBase) -> list[str]:
    partners = kb._data.get("partners") or {}
    refs = partners.get("registered_sources") or []
    return [str(s) for s in refs]