"""Scheme-aware financial fit (M2 §5).

Computes, per scheme, the eligible/maximum financing from the M1 financial
parameters and the request, honouring inclusive/exclusive bounds exactly as
stored (TL lower bound exclusive -> min_inclusive is false).

Financial parameters are read from the KB, never hardcoded here. ELS uses the
KB formula min(40L, 90% x course_fee) -> calculated, not textual (M2 §10).
"""

from __future__ import annotations

from typing import Any, Optional

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import Verdict
from intelligence.models.result import (
    ConditionalResolution,
    FinancialConstraint,
    FinancialFitResult,
)
from intelligence.normalization.profile import NormalizedProfile
from intelligence.normalization.requirement import NormalizedRequirement
from intelligence.explanations import reason_keys as RK


def finance_fit(
    kb: KnowledgeBase,
    scheme_id: str,
    req: NormalizedRequirement,
    profile: NormalizedProfile,
) -> FinancialFitResult:
    scheme = kb.scheme(scheme_id)
    if scheme is None:  # pragma: no cover - guarded by engine
        raise ValueError(f"unknown scheme: {scheme_id}")

    is_education = bool((scheme.get("education") or {}).get("is_education_scheme"))

    if is_education:
        return _education_finance_fit(kb, scheme_id, req, profile)
    return _income_finance_fit(kb, scheme_id, req, profile)


# ---------------------------------------------------------------- income
def _income_finance_fit(kb, scheme_id, req, profile) -> FinancialFitResult:
    scheme = kb.scheme(scheme_id)
    cost = req.project_cost
    requested = req.requested_loan_amount
    reason_keys: list[str] = []
    constraints: list[FinancialConstraint] = []

    cb = scheme.get("cost_bounds") or {}
    if cost is None:
        return FinancialFitResult(
            scheme_id=scheme_id,
            status=Verdict.UNKNOWN,
            project_cost=None,
            requested_amount=requested,
            reason_keys=[RK.MISSING_PROJECT_COST],
            sources=_scheme_sources(kb, scheme_id),
            data_quality_issues=list(scheme.get("data_quality_issues") or []),
        )

    # Cost bounds (inclusivity flags from the scheme, never assumed).
    min_v, min_inc = cb.get("min"), cb.get("min_inclusive")
    max_v, max_inc = cb.get("max"), cb.get("max_inclusive")

    if min_v is not None:
        ok = cost > float(min_v) if min_inc is False else cost >= float(min_v)
        constraints.append(FinancialConstraint(
            parameter="project_cost_min",
            label="Project cost minimum",
            expected=min_v,
            actual=cost,
            passed=ok,
            inclusivity="exclusive" if min_inc is False else "inclusive",
            source_ids=_scheme_sources(kb, scheme_id),
        ))
        if not ok:
            reason_keys.append(RK.PROJECT_COST_BELOW_MIN)

    if max_v is not None:
        ok = cost < float(max_v) if max_inc is False else cost <= float(max_v)
        constraints.append(FinancialConstraint(
            parameter="project_cost_max",
            label="Project cost maximum",
            expected=max_v,
            actual=cost,
            passed=ok,
            inclusivity="exclusive" if max_inc is False else "inclusive",
            source_ids=_scheme_sources(kb, scheme_id),
        ))
        if not ok:
            reason_keys.append(RK.PROJECT_COST_ABOVE_MAX)

    financing = scheme.get("financing_percent")
    loan_max = (scheme.get("loan_bounds") or {}).get("max")
    eligible = None
    if financing is not None:
        base = (float(financing) / 100.0) * float(cost)
        eligible = min(base, float(loan_max)) if loan_max is not None else base

    # requested loan constraint
    loan_reason_ok = None
    if requested is not None and eligible is not None:
        ok = requested <= eligible
        constraints.append(FinancialConstraint(
            parameter="loan_amount",
            label="Requested loan amount",
            expected=eligible,
            actual=requested,
            passed=ok,
            inclusivity="inclusive",
            source_ids=_scheme_sources(kb, scheme_id),
        ))
        if ok:
            reason_keys.append(RK.FINANCIAL_AMOUNT_WITHIN_LIMIT)
            loan_reason_ok = True
        else:
            reason_keys.append(RK.FINANCIAL_AMOUNT_EXCEEDS_LIMIT)
            loan_reason_ok = False

    failed = [c for c in constraints if not c.passed]
    if failed:
        status = Verdict.FAIL
    elif any(c.passed is False for c in constraints) is None and constraints and not reason_keys:
        status = Verdict.PASS
    else:
        status = Verdict.PASS if constraints else Verdict.UNKNOWN

    return FinancialFitResult(
        scheme_id=scheme_id,
        status=status,
        project_cost=cost,
        requested_amount=requested,
        eligible_amount=eligible,
        max_possible_amount=eligible,
        financing_percent=financing,
        constraints=constraints,
        conditionals=resolve_conditionals(kb, scheme_id, profile, req),
        reason_keys=sorted(set(reason_keys)),
        sources=_scheme_sources(kb, scheme_id),
        data_quality_issues=list(scheme.get("data_quality_issues") or []),
    )


# ------------------------------------------------------------- education (ELS)
def _education_finance_fit(kb, scheme_id, req, profile) -> FinancialFitResult:
    scheme = kb.scheme(scheme_id)
    fee = req.education_fee
    requested = req.requested_loan_amount
    constraints: list[FinancialConstraint] = []
    reason_keys: list[str] = []
    formula_detail = None
    max_possible = None

    cap = None
    formula_fp = kb.fp(scheme_id, "loan_cap_formula")
    loan_max = (scheme.get("loan_bounds") or {}).get("max")

    if fee is None:
        return FinancialFitResult(
            scheme_id=scheme_id,
            status=Verdict.UNKNOWN,
            requested_amount=requested,
            reason_keys=[RK.MISSING_COURSE_FEE],
            sources=_scheme_sources(kb, scheme_id),
            data_quality_issues=_scheme_dq(kb, scheme_id),
        )

    if formula_fp:
        try:
            cap, formula_detail = kb.evaluate_formula(formula_fp["value"], {"course_fee": float(fee)})
        except ValueError:
            cap = None
    if cap is None:
        cap = loan_max
    cap = float(cap)
    max_possible = min(cap, float(loan_max)) if loan_max is not None else cap

    constraints.append(FinancialConstraint(
        parameter="loan_cap_formula",
        label="ELS loan cap min(40L, 90% of course fee)",
        expected=cap,
        actual=fee,
        passed=True,
        source_ids=_scheme_sources(kb, scheme_id),
    ))
    reason_keys.append(RK.ELS_CAP_APPLIED)

    # Optional project-cost bound for ELS when the request supplies a cost figure.
    cost = req.project_cost
    cb = scheme.get("cost_bounds") or {}
    if cost is not None and cb.get("max") is not None:
        ok = float(cost) <= float(cb["max"])
        constraints.append(FinancialConstraint(
            parameter="project_cost_max",
            label="ELS project cost maximum",
            expected=cb["max"],
            actual=cost,
            passed=ok,
            inclusivity="inclusive",
            source_ids=_scheme_sources(kb, scheme_id),
        ))
        if not ok:
            reason_keys.append(RK.PROJECT_COST_ABOVE_MAX)

    if requested is not None and max_possible is not None:
        ok = requested <= max_possible
        constraints.append(FinancialConstraint(
            parameter="loan_amount",
            label="Requested loan amount",
            expected=max_possible,
            actual=requested,
            passed=ok,
            inclusivity="inclusive",
            source_ids=_scheme_sources(kb, scheme_id),
        ))
        if ok:
            reason_keys.append(RK.FINANCIAL_AMOUNT_WITHIN_LIMIT)
        else:
            reason_keys.append(RK.FINANCIAL_AMOUNT_EXCEEDS_LIMIT)

    failed = [c for c in constraints if not c.passed]
    status = Verdict.FAIL if failed else Verdict.PASS

    return FinancialFitResult(
        scheme_id=scheme_id,
        status=status,
        course_fee=fee,
        project_cost=cost,
        requested_amount=requested,
        eligible_amount=max_possible,
        max_possible_amount=max_possible,
        financing_percent=(scheme.get("financing_percent")),
        constraints=constraints,
        conditionals=resolve_conditionals(kb, scheme_id, profile, req),
        formula_detail=formula_detail,
        reason_keys=sorted(set(reason_keys)),
        sources=_scheme_sources(kb, scheme_id),
        data_quality_issues=_scheme_dq(kb, scheme_id),
    )


# ------------------------------------------------------------- conditionals
def resolve_conditionals(
    kb: KnowledgeBase,
    scheme_id: str,
    profile: NormalizedProfile,
    req: NormalizedRequirement,
) -> list[ConditionalResolution]:
    """Resolve conditional KB values (rates/repayment/moratorium) against user inputs.

    These are informational for the frontend; a missing conditional input is
    surfaced as UNKNOWN (CONDITIONAL_VALUE_UNKNOWN), never guessed.
    """
    out: list[ConditionalResolution] = []
    ctx = {
        "channel_type": req.channel_type,
        "activity_category": req.activity_category,
        "repayment_has_started": req.repayment_has_started,
    }
    params = [
        ("beneficiary_interest_rate", "beneficiary rate (% p.a.)"),
        ("repayment_period_years", "repayment (years)"),
        ("moratorium_months", "moratorium"),
    ]
    for parameter, label in params:
        fp = kb.fp(scheme_id, parameter)
        if fp is None:
            continue
        value = fp.get("value")
        if isinstance(value, dict) and value.get("type") == "conditional":
            resolved, ok = kb.resolve_conditional(value, ctx)
            out.append(ConditionalResolution(
                parameter=parameter,
                variable=value.get("variable") or "",
                resolved=ok,
                value=None if not ok else resolved,
                reason_key="" if ok else RK.CONDITIONAL_VALUE_UNKNOWN,
                note=fp.get("value_original") or "",
            ))
    return out


def _scheme_sources(kb: KnowledgeBase, scheme_id: str) -> list[str]:
    scheme = kb.scheme(scheme_id)
    return list(scheme.get("sources") or [])


def _scheme_dq(kb: KnowledgeBase, scheme_id: str) -> list[str]:
    scheme = kb.scheme(scheme_id)
    return list(scheme.get("data_quality_issues") or [])