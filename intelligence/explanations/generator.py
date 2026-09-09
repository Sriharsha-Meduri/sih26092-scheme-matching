"""Structured, fact-backed explanation generation (M2 §10).

The engine emits stable reason keys + source references computed from the actual
decision objects — never free-form text, never hallucinated content. Reasons are
grouped for the frontend; warnings carry provenance/verification flags the UI
should surface.
"""

from __future__ import annotations

from typing import Optional

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import (
    MatchStatus,
    Purpose,
    VerificationStatus,
    Verdict,
)
from intelligence.models.result import (
    ActivityMatchResult,
    EducationFitResult,
    EligibilityResult,
    FinancialFitResult,
    PartnerFitResult,
    SchemeRecommendation,
    SourceRef,
)
from intelligence.explanations import reason_keys as RK

# canonical input field that a KB rule field depends on (for gaps)
RULE_FIELD_TO_INPUT = {
    "community": "community",
    "annual_family_income": "annual_family_income",
    "caste_certificate": "caste_certificate",
    "entity_type": "entity_type",
}


def collect_reasons(
    eligibility: EligibilityResult,
    activity: ActivityMatchResult,
    financial: FinancialFitResult,
    education: EducationFitResult,
    partner: PartnerFitResult,
    purpose: Purpose,
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    # eligibility PASS reasons
    for rule in eligibility.rule_results:
        if rule.result is Verdict.PASS and rule.reason_key not in reasons:
            reasons.append(rule.reason_key)

    # activity
    if activity.status is MatchStatus.MATCH:
        if activity.reason_key not in reasons:
            reasons.append(activity.reason_key)
        if activity.verification is VerificationStatus.UNVERIFIED and RK.ACTIVITY_UNVERIFIED not in warnings:
            warnings.append(RK.ACTIVITY_UNVERIFIED)
    elif activity.status is MatchStatus.NO_MATCH:
        if RK.ACTIVITY_NO_MATCH not in reasons:
            reasons.append(RK.ACTIVITY_NO_MATCH)
    elif activity.status is MatchStatus.UNKNOWN and financial is not None:
        if activity.raw_activity is not None and activity.reason_key == RK.ACTIVITY_UNSUPPORTED:
            if RK.ACTIVITY_UNSUPPORTED not in reasons:
                reasons.append(RK.ACTIVITY_UNSUPPORTED)
        elif RK.MISSING_ACTIVITY not in reasons:
            reasons.append(RK.MISSING_ACTIVITY)

    # financial
    for key in financial.reason_keys:
        if key not in reasons:
            reasons.append(key)
    if financial.status is Verdict.PASS and financial.reason_keys == []:
        if RK.FINANCIAL_OK not in reasons:
            reasons.append(RK.FINANCIAL_OK)
    for cond in financial.conditionals:
        if not cond.resolved and RK.CONDITIONAL_VALUE_UNKNOWN not in warnings:
            warnings.append(RK.CONDITIONAL_VALUE_UNKNOWN)

    # education
    if education.status is MatchStatus.MATCH and RK.COURSE_COVERED not in reasons:
        reasons.append(RK.COURSE_COVERED)
    elif education.status is MatchStatus.NO_MATCH and RK.COURSE_NOT_COVERED not in reasons:
        reasons.append(RK.COURSE_NOT_COVERED)

    # partner
    if partner.score == 0:
        if RK.PARTNER_DATA_UNAVAILABLE not in warnings:
            warnings.append(RK.PARTNER_DATA_UNAVAILABLE)

    return reasons, warnings


def collect_sources(
    kb: KnowledgeBase,
    scheme_id: str,
    eligibility: EligibilityResult,
    activity: ActivityMatchResult,
    financial: FinancialFitResult,
    education: EducationFitResult,
    partner: PartnerFitResult,
) -> list[SourceRef]:
    ids: list[str] = []
    order: list[str] = []
    for rule in eligibility.rule_results:
        for s in rule.sources:
            if s not in ids:
                ids.append(s)
                order.append(s)
    for s in activity.mapping_sources:
        if s not in ids:
            ids.append(s)
            order.append(s)
    for s in financial.sources:
        if s not in ids:
            ids.append(s)
            order.append(s)
    for s in education.sources:
        if s not in ids:
            ids.append(s)
            order.append(s)
    for s in partner.sources:
        if s not in ids:
            ids.append(s)
            order.append(s)

    refs: list[SourceRef] = []
    for s in order:
        refs.append(SourceRef(
            source_id=s,
            title=kb.source_title(s),
            url=kb.source_url(s),
            role="PRIMARY" if s in financial.sources else "CORROBORATING",
        ))
    return refs


def attach_to_recommendation(
    kb: KnowledgeBase,
    rec: SchemeRecommendation,
    purpose: Purpose,
) -> None:
    reasons, warnings = collect_reasons(
        rec.eligibility, rec.activity_match, rec.financial_fit,
        rec.education_fit, rec.partner_fit, purpose,
    )
    rec.reasons = list(dict.fromkeys(reasons))
    rec.warnings = list(dict.fromkeys(warnings))
    rec.sources = collect_sources(
        kb, rec.scheme_id, rec.eligibility, rec.activity_match,
        rec.financial_fit, rec.education_fit, rec.partner_fit,
    )