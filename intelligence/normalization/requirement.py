"""Requirement normalization (M2 §6).

Combines raw requirement text/numbers into a canonical, validated view used by
candidate discovery and the matching modules. Also fixes purpose when omitted:
education wins only when course inputs exist and no business activity is given
(the PRD education scenarios omit activity); otherwise business/income.

Determinism: same raw requirement -> same NormalizedRequirement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import MatchStatus, Purpose
from intelligence.models.requirement import Requirement
from intelligence.normalization.activity import ActivityResolution, resolve_activity
from intelligence.normalization.education import CourseResolution, resolve_course
from intelligence.normalization.finance import parse_inr

Number = Union[int, float]


@dataclass
class NormalizedRequirement:
    purpose: Purpose = Purpose.UNKNOWN
    requirement_type: Optional[str] = None
    activity_raw: Optional[str] = None
    activity: ActivityResolution = field(default_factory=lambda: ActivityResolution(raw=None))
    project_cost: Optional[Number] = None
    requested_loan_amount: Optional[Number] = None
    course: Optional[str] = None
    course_family: Optional[str] = None
    education_fee: Optional[Number] = None
    course_duration_years: Optional[Number] = None
    institution_type: Optional[str] = None
    channel_type: Optional[str] = None
    activity_category: Optional[str] = None
    repayment_has_started: Optional[bool] = None
    course_resolution: CourseResolution = field(
        default_factory=lambda: CourseResolution(status=MatchStatus.UNKNOWN)
    )


def normalize_requirement(requirement: Requirement, kb: KnowledgeBase) -> NormalizedRequirement:
    if not isinstance(requirement, Requirement):
        raise TypeError("requirement must be a Requirement")

    purpose = _resolve_purpose(requirement)
    activity_resolution = resolve_activity(
        requirement.activity if purpose is not Purpose.EDUCATION else None, kb
    )
    course_resolution = resolve_course(
        requirement.course, requirement.course_family, kb
    )

    return NormalizedRequirement(
        purpose=purpose,
        requirement_type=requirement.requirement_type,
        activity_raw=requirement.activity,
        activity=activity_resolution,
        project_cost=parse_inr(requirement.project_cost),
        requested_loan_amount=parse_inr(requirement.requested_loan_amount),
        course=requirement.course,
        course_family=requirement.course_family,
        education_fee=parse_inr(requirement.education_fee),
        course_duration_years=_to_number(requirement.course_duration_years),
        institution_type=requirement.institution_type,
        channel_type=requirement.channel_type,
        activity_category=requirement.activity_category,
        repayment_has_started=requirement.repayment_has_started,
        course_resolution=course_resolution,
    )


def _resolve_purpose(req: Requirement) -> Purpose:
    explicit = _clean(req.purpose)
    has_course = bool(_clean(req.course) or _clean(req.course_family))
    has_activity = bool(_clean(req.activity))

    if explicit == "education":
        return Purpose.EDUCATION
    if explicit == "business" or explicit in ("income", "income-generating"):
        return Purpose.BUSINESS
    # omitted purpose: infer deterministically from which decision inputs exist
    if has_course and not has_activity:
        return Purpose.EDUCATION
    if has_activity:
        return Purpose.BUSINESS
    if has_course:
        return Purpose.EDUCATION
    return Purpose.UNKNOWN


def _clean(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _to_number(value: Optional[Union[str, Number]]) -> Optional[Number]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_requirement(requirement: Requirement) -> None:
    for name in ("project_cost", "requested_loan_amount", "education_fee"):
        value = getattr(requirement, name)
        if value is not None:
            parse_inr(value)
    if requirement.course_duration_years is not None and _to_number(requirement.course_duration_years) is None:
        raise ValueError("course_duration_years must be numeric or None")