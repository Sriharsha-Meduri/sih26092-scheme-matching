"""Gap detection (M2 §11, §13).

Missing information is derived ONLY from the structured decision results: a
field is "missing" when an applicable rule or matcher hit UNKNOWN because the
input value was absent (None). Provided-but-unresolvable inputs (e.g. an
activity string that matches nothing) are NOT gaps — they are surfaced as
UNSUPPORTED_ACTIVITY semantics, which is a different state.

Aggregated globally so one request answers "what else do you need to tell us".
"""

from __future__ import annotations

from collections import OrderedDict

from intelligence.models.enums import MatchStatus, Verdict
from intelligence.models.result import (
    ActivityMatchResult,
    EducationFitResult,
    EligibilityResult,
    FinancialFitResult,
    MissingFieldEntry,
    SchemeRecommendation,
)
from intelligence.explanations import reason_keys as RK

REASON_TO_FIELD = {
    RK.MISSING_COMMUNITY: "community",
    RK.MISSING_ANNUAL_INCOME: "annual_family_income",
    RK.MISSING_CASTE_CERTIFICATE: "caste_certificate",
    RK.MISSING_ENTITY_TYPE: "entity_type",
    RK.MISSING_ACTIVITY: "activity",
    RK.MISSING_PROJECT_COST: "project_cost",
    RK.MISSING_COURSE_FEE: "education_fee",
    RK.MISSING_COURSE: "course",
}


def detect_missing_fields(
    eligibility: EligibilityResult,
    activity: ActivityMatchResult,
    financial: FinancialFitResult,
    education: EducationFitResult,
) -> dict[str, list[str]]:
    """Per-canónica field -> list of reason keys, for one scheme candidate."""
    missing: dict[str, list[str]] = OrderedDict()

    def _add(reason: str) -> None:
        field = REASON_TO_FIELD.get(reason)
        if field is None:
            return
        missing.setdefault(field, [])
        if reason not in missing[field]:
            missing[field].append(reason)

    for rule in eligibility.rule_results:
        if rule.result is Verdict.UNKNOWN:
            _add(rule.reason_key)

    if activity.status is MatchStatus.UNKNOWN:
        _add(activity.reason_key)

    if financial.status is Verdict.UNKNOWN:
        for reason in financial.reason_keys:
            _add(reason)

    if education.status is MatchStatus.UNKNOWN:
        _add(education.reason_key)

    return missing


def aggregate_missing_fields(
    recommendations: list[SchemeRecommendation],
    excluded: list,
) -> list[MissingFieldEntry]:
    """Collapse per-scheme gaps + excluded-information gaps into request scope."""
    by_field: dict[str, dict[str, list[str]]] = OrderedDict()

    def _absorb(field: str, scheme_id: str, reasons: list[str]) -> None:
        entry = by_field.setdefault(field, {"scheme_ids": [], "reasons": []})
        if scheme_id not in entry["scheme_ids"]:
            entry["scheme_ids"].append(scheme_id)
        for r in reasons:
            if r not in entry["reasons"]:
                entry["reasons"].append(r)

    for rec in recommendations:
        for field, reasons in detect_missing_fields(
            rec.eligibility, rec.activity_match, rec.financial_fit, rec.education_fit
        ).items():
            _absorb(field, rec.scheme_id, reasons)

    # excluded schemes that were dropped for UNKNOWN reasons also contribute gaps
    for ex in excluded:
        if getattr(ex, "eligibility_verdict", None) is Verdict.UNKNOWN:
            for reason in getattr(ex, "reason_keys", []) or [ex.reason_key]:
                field = REASON_TO_FIELD.get(reason)
                if field:
                    _absorb(field, ex.scheme_id, [reason])

    return [
        MissingFieldEntry(field=field, scheme_ids=entry["scheme_ids"], reason_keys=entry["reasons"])
        for field, entry in by_field.items()
    ]