"""Rule scope + condition-group semantics (M2 §8).

Eligibility rules live in the KB as data; this module only decides *which* rules
apply to a scheme (via scope objects) and *how* to combine them:

- rules sharing a condition_group are OR-combined  (e.g. E004..E006
  "ENTITY_TYPE_ALLOWED": the applicant may be Individual OR Partnership Firm OR
  Co-operative Society),
- ungrouped rules are AND-combined across groups (E001/E002/E003 must all pass),
- EXTERNAL_DOMAIN rules (E007) never apply to loan eligibility.

One FAIL group fails the scheme; else any UNKNOWN group -> UNKNOWN; else PASS.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Optional

from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import Verdict


def applicable_rules(kb: KnowledgeBase, scheme_id: str) -> list[dict]:
    return kb.rules_for_scheme(scheme_id)


def group_rules(rules: list[dict]) -> list[list[dict]]:
    """Stable partition of rules into OR-groups.

    Rules that share a `condition_group` are OR-combined (e.g. E004..E006
    ENTITY_TYPE_ALLOWED: Individual OR Partnership OR Co-operative). Ungrouped
    rules each form their OWN group so they are AND-combined afterwards —
    E001/E002/E003 must all pass; they must never be OR'd together.
    """
    groups: list[list[dict]] = [[r] for r in rules if not (r.get("condition_group"))]
    buckets: "OrderedDict[str | None, list[dict]]" = OrderedDict()
    for rule in rules:
        key = rule.get("condition_group")
        if key:
            buckets.setdefault(key, []).append(rule)
    groups.extend(buckets.values())
    return groups


def combine(group_verdicts: list[Verdict]) -> Verdict:
    if any(v is Verdict.FAIL for v in group_verdicts):
        return Verdict.FAIL
    if any(v is Verdict.UNKNOWN for v in group_verdicts):
        return Verdict.UNKNOWN
    if all(v is Verdict.PASS for v in group_verdicts):
        return Verdict.PASS
    return Verdict.FAIL


def or_combine(rule_verdicts: list[Verdict]) -> Verdict:
    if any(v is Verdict.PASS for v in rule_verdicts):
        return Verdict.PASS
    if any(v is Verdict.UNKNOWN for v in rule_verdicts):
        return Verdict.UNKNOWN
    if rule_verdicts:
        return Verdict.FAIL
    return Verdict.NOT_APPLICABLE