"""Education/course matching for ELS (M2 §6).

Uses the M1 education knowledge (25 covered course families) only. Course text
is resolved to a family (via family names, raw_text, or levels); coverage is
read straight from the KB record (`coverage_status`). When the course/family is
not resolvable or not listed, the result is NO_MATCH/UNKNOWN — never inferred.
"""

from __future__ import annotations

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import MatchStatus, VerificationStatus
from intelligence.models.result import EducationFitResult
from intelligence.explanations import reason_keys as RK
from intelligence.normalization.education import CourseResolution, resolve_course
from intelligence.normalization.requirement import NormalizedRequirement


def match_education(
    kb: KnowledgeBase,
    req: NormalizedRequirement,
    scheme_id: str,
) -> EducationFitResult:
    scheme = kb.scheme(scheme_id)
    if scheme is None or not (scheme.get("education") or {}).get("is_education_scheme"):
        return EducationFitResult(scheme_id=scheme_id, status=MatchStatus.NOT_APPLICABLE,
                                  reason_key=RK.COURSE_COVERED)

    res: CourseResolution = resolve_course(req.course, req.course_family, kb)

    if not (req.course or req.course_family):
        return EducationFitResult(
            scheme_id=scheme_id,
            status=MatchStatus.UNKNOWN,
            reason_key=RK.MISSING_COURSE,
            course=req.course,
        )

    if res.status is MatchStatus.MATCH:
        return EducationFitResult(
            scheme_id=scheme_id,
            status=MatchStatus.MATCH,
            reason_key=RK.COURSE_COVERED,
            course=req.course,
            course_family=req.course_family,
            matched_family_id=res.matched_family_id,
            matched_family_name=res.matched_family_name,
            levels=res.levels,
            coverage_status=res.coverage_status,
            verification=VerificationStatus.VERIFIED,
            sources=_family_sources(kb, res.matched_family_id),
        )
    if res.status is MatchStatus.NO_MATCH:
        return EducationFitResult(
            scheme_id=scheme_id,
            status=MatchStatus.NO_MATCH,
            reason_key=RK.COURSE_NOT_COVERED,
            course=req.course,
            course_family=req.course_family,
            sources=_family_sources(kb, res.matched_family_id),
        )
    return EducationFitResult(
        scheme_id=scheme_id,
        status=MatchStatus.UNKNOWN,
        reason_key=RK.COURSE_COVERAGE_UNKNOWN,
        course=req.course,
        course_family=req.course_family,
    )


def _family_sources(kb: KnowledgeBase, family_id: str | None) -> list[str]:
    if not family_id:
        return []
    fam = kb.family(family_id)
    return list(fam.get("sources") or []) if fam else []