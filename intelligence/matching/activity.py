"""Activity->scheme matching (M2 §4).

Uses the M1 activity taxonomy plus the activity->scheme mapping only. States:
  MATCH                activity resolves and maps to this scheme
  NO_MATCH             activity resolves but is not mapped to this scheme
  UNKNOWN              activity missing or not in the taxonomy
  NOT_APPLICABLE       education case (activity is not used for ELS)

Every current activity mapping is UNVERIFIED (DQ-012); that status is preserved
and exposed as a warning, never silently promoted to a verified fact.
"""

from __future__ import annotations

from typing import Optional

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import (
    MatchStatus,
    Purpose,
    VerificationStatus,
)
from intelligence.models.result import ActivityMatchResult
from intelligence.explanations import reason_keys as RK
from intelligence.normalization.activity import ActivityResolution


def match_activity(
    kb: KnowledgeBase,
    scheme_id: str,
    resolution: ActivityResolution,
    purpose: Purpose,
) -> ActivityMatchResult:
    if purpose is Purpose.EDUCATION or (scheme_id == "NSFDC-ELS" and resolution.raw is None):
        return ActivityMatchResult(
            scheme_id=scheme_id,
            status=MatchStatus.NOT_APPLICABLE,
            reason_key=RK.ACTIVITY_MATCH,
            raw_activity=resolution.raw,
        )

    if resolution.raw is None:
        return ActivityMatchResult(
            scheme_id=scheme_id,
            status=MatchStatus.UNKNOWN,
            reason_key=RK.MISSING_ACTIVITY,
            raw_activity=None,
        )

    if not resolution.resolved:
        return ActivityMatchResult(
            scheme_id=scheme_id,
            status=MatchStatus.UNKNOWN,
            reason_key=RK.ACTIVITY_UNSUPPORTED,
            raw_activity=resolution.raw,
        )

    mapped_ids = kb.activity_scheme_ids(resolution.canonical_activity_id)
    if scheme_id in mapped_ids:
        mapping = kb.activity_mapping(resolution.canonical_activity_id)
        status = mapping.get("status") if mapping else None
        verification = VerificationStatus.UNVERIFIED if status == "UNVERIFIED" else VerificationStatus.VERIFIED
        return ActivityMatchResult(
            scheme_id=scheme_id,
            status=MatchStatus.MATCH,
            reason_key=RK.ACTIVITY_MATCH,
            raw_activity=resolution.raw,
            canonical_activity_id=resolution.canonical_activity_id,
            canonical_activity_name=resolution.canonical_activity_name,
            sector_ids=resolution.sector_ids,
            verification=verification,
            mapping_sources=resolution.mapping_sources,
            notes=resolution.notes,
        )

    return ActivityMatchResult(
        scheme_id=scheme_id,
        status=MatchStatus.NO_MATCH,
        reason_key=RK.ACTIVITY_NO_MATCH,
        raw_activity=resolution.raw,
        canonical_activity_id=resolution.canonical_activity_id,
        canonical_activity_name=resolution.canonical_activity_name,
        sector_ids=resolution.sector_ids,
    )