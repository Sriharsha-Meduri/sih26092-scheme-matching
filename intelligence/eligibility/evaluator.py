"""Deterministic per-scheme eligibility evaluation (M2 §8).

Pipeline per candidate scheme:
  KB rules applicable to the scheme (scope-resolved)
    -> group into OR-clusters (condition_group)
    -> evaluate each rule against the canonical profile context
    -> combine clusters into a scheme verdict (PASS / FAIL / UNKNOWN)

Result carries every rule evaluation (rule_id, field, operator, expected,
actual, verdict, reason key, sources) so the explanation + gap layers run
purely off these structured facts.
"""

from __future__ import annotations

from intelligence.kb.repository import KnowledgeBase
from intelligence.eligibility.operators import apply_operator
from intelligence.models.enums import VerificationStatus, Verdict
from intelligence.models.result import EligibilityResult, RuleResult
from intelligence.explanations import reason_keys as RK

# field -> reason key per outcome bucket
_PASS_KEYS = {
    "community": RK.COMMUNITY_MATCH,
    "annual_family_income": RK.INCOME_WITHIN_LIMIT,
    "caste_certificate": RK.CASTE_CERTIFICATE_EXISTS,
    "entity_type": RK.ENTITY_TYPE_ALLOWED,
}
_FAIL_KEYS = {
    "community": RK.COMMUNITY_MISMATCH,
    "annual_family_income": RK.INCOME_EXCEEDS_LIMIT,
    "caste_certificate": RK.CASTE_CERTIFICATE_MISSING,
    "entity_type": RK.ENTITY_TYPE_NOT_ALLOWED,
}
_UNKNOWN_KEYS = {
    "community": RK.MISSING_COMMUNITY,
    "annual_family_income": RK.MISSING_ANNUAL_INCOME,
    "caste_certificate": RK.MISSING_CASTE_CERTIFICATE,
    "entity_type": RK.MISSING_ENTITY_TYPE,
}


def evaluate_scheme(kb: KnowledgeBase, scheme_id: str, context: dict) -> EligibilityResult:
    """Evaluate all applicable rules for one scheme. context = canonical profile dict."""
    from intelligence.eligibility.rules import group_rules, or_combine, combine

    rules = kb.rules_for_scheme(scheme_id)
    if not rules:
        return EligibilityResult(scheme_id=scheme_id, verdict=Verdict.NOT_APPLICABLE,
                                 verification=VerificationStatus.VERIFIED)

    results: list[RuleResult] = []

    for rule in rules:
        results.append(_evaluate_rule(rule, context))

    groups = group_rules(rules)
    group_verdicts: list[Verdict] = []
    idx = 0
    for group in groups:
        verdicts = [results[m].result for m in range(idx, idx + len(group))]
        idx += len(group)
        group_verdicts.append(or_combine(verdicts))

    verdict = combine(group_verdicts)
    if verdict is Verdict.NOT_APPLICABLE:  # pragma: no cover - defensive
        verdict = Verdict.UNKNOWN

    verification = (
        VerificationStatus.UNVERIFIED
        if any(r.result is Verdict.UNKNOWN for r in results)
        else VerificationStatus.VERIFIED
    )
    return EligibilityResult(
        scheme_id=scheme_id,
        verdict=verdict,
        rule_results=results,
        verification=verification,
        passed_rule_ids=[r.rule_id for r in results if r.result is Verdict.PASS],
        failed_rule_ids=[r.rule_id for r in results if r.result is Verdict.FAIL],
        unknown_rule_ids=[r.rule_id for r in results if r.result is Verdict.UNKNOWN],
    )


def _evaluate_rule(rule: dict, context: dict) -> RuleResult:
    rule_id = rule["id"]
    field = rule["field"]
    operator = rule["operator"]
    expected = rule.get("value")
    actual = context.get(field)
    outcome = apply_operator(operator, expected, actual)

    result = Verdict.PASS if outcome is True else Verdict.FAIL if outcome is False else Verdict.UNKNOWN
    key = _select_reason(result, field)

    scope_type = (rule.get("scope") or {}).get("type", "")
    return RuleResult(
        rule_id=rule_id,
        name=rule.get("name") or rule_id,
        field=field,
        operator=operator,
        expected_value=expected,
        actual_value=actual,
        result=result,
        reason_key=key,
        scope_type=scope_type,
        sources=list(rule.get("sources") or []),
        data_quality_issues=list(rule.get("data_quality_issues") or []),
    )


def _select_reason(result: Verdict, field: str) -> str:
    bucket = {
        Verdict.PASS: _PASS_KEYS,
        Verdict.FAIL: _FAIL_KEYS,
        Verdict.UNKNOWN: _UNKNOWN_KEYS,
    }[result]
    return bucket.get(field, RK.RULE_PASS if result is Verdict.PASS else
                      RK.RULE_FAIL if result is Verdict.FAIL else RK.INSUFFICIENT_INFORMATION)