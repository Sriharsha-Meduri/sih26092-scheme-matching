"""Education/course normalization (M2 §6, §11).

Resolves raw course text and/or a course family to an M1 covered course family
(25 families, education.json). A raw course such as "B.Tech" resolves through
the family's levels/raw_text; a course_family string resolves against the
family names. No invented coverage: an unresolved course stays UNKNOWN/NO_MATCH
(exactly what G011 encodes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import MatchStatus, VerificationStatus


@dataclass
class CourseResolution:
    course: Optional[str] = None
    course_family: Optional[str] = None
    matched_family_id: Optional[str] = None
    matched_family_name: Optional[str] = None
    levels: list[str] = field(default_factory=list)
    coverage_status: Optional[str] = None
    status: MatchStatus = MatchStatus.UNKNOWN
    verification: Optional[VerificationStatus] = None


def resolve_course(course: Optional[str], course_family: Optional[str],
                   kb: KnowledgeBase) -> CourseResolution:
    """Match user course inputs to a covered family (course wins over family when both given
    and a match exists; otherwise family decides)."""
    base = CourseResolution(course=course, course_family=course_family,
                            verification=VerificationStatus.VERIFIED)

    candidate = None
    if course:
        candidate = kb.resolve_course(course)
        if candidate is None and course_family:
            candidate = kb.resolve_course(course_family)
    elif course_family:
        candidate = kb.resolve_course(course_family)

    if candidate is None:
        # A user-provided course_family is a covered-list position: not listed
        # is definitively NO_MATCH (G011). An unresolvable raw course string is
        # just UNKNOWN — we cannot tell without fabricating coverage.
        base.status = MatchStatus.NO_MATCH if course_family else MatchStatus.UNKNOWN
        return base

    base.matched_family_id = candidate["id"]
    base.matched_family_name = candidate["family"]
    base.levels = list(candidate.get("levels") or [])
    base.coverage_status = candidate.get("coverage_status")
    noted = candidate.get("coverage_status")
    if noted == "LISTED_IN_COVERED_COURSES":
        base.status = MatchStatus.MATCH
    elif noted in (None, "NOT_SPECIFIED"):
        base.status = MatchStatus.UNKNOWN
    else:
        base.status = MatchStatus.NO_MATCH
    return base