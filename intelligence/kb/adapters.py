"""Pure adapters: KB value semantics turned into engine helpers.

These mirror the M1 oracle behavior (KB/tests/test_kb_golden.py) which the M1
report mandates the real engine reproduce — implemented here as clean typed
helpers instead of the test-side sketch:
  - conditional_value resolution against a user context,
  - formula evaluation (ELS cap = min(40L, 90% x course_fee)),
  - normalized keys for lookup (case/space-insensitive).

All functions are deterministic and side-effect free.
"""

from __future__ import annotations

import re
from typing import Any

# when-map keys emitted by the M1 normalizer.
_EQ = "=="
_IN = "IN"
_NOT_IN = "NOT_IN"

CONDITION_KEYS = {_EQ, _IN, _NOT_IN}


def normalize_key(text: str) -> str:
    """Number/letter key for case- and whitespace-insensitive lookups."""
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def resolve_conditional(value: Any, context: dict[str, Any]) -> tuple[Any, bool]:
    """Resolve a KB conditional_value against a context.

    Returns (resolved_value | None, ok). ok=False when the required variable is
    missing from the context (the caller must surface UNKNOWN, never guess).
    Scalars pass through unchanged (ok=True).
    """
    if not (isinstance(value, dict) and value.get("type") == "conditional"):
        return value, True
    variable = value.get("variable")
    actual = context.get(variable) if variable is not None else None
    branch = _match_branch(value["branches"], actual)
    if branch is None or actual is None:
        return None, False
    return branch["value"], True


def _match_branch(branches: list[dict], actual: Any) -> dict | None:
    if actual is None:
        return None
    for branch in branches:
        when = branch.get("when", {})
        if set(when.keys()).intersection(CONDITION_KEYS):
            if _EQ in when and actual == when[_EQ]:
                return branch
            if _IN in when and actual in when[_IN]:
                return branch
            if _NOT_IN in when and actual not in when[_NOT_IN]:
                return branch
    return None


def evaluate_formula(value: Any, context: dict[str, Any]) -> tuple[Any, str | None]:
    """Evaluate a KB formula object (e.g. ELS loan cap).

    Returns (result, human detail). Scalars pass through unchanged.
    Raises ValueError when the formula needs input the context does not provide
    (caller converts to UNKNOWN).
    """
    if not (isinstance(value, dict) and value.get("type") == "formula"):
        return value, None
    kind = value.get("kind")
    terms = value.get("terms", [])
    if kind != "min":
        raise ValueError(f"unsupported formula kind: {kind}")
    values: list[Any] = []
    parts: list[str] = []
    for term in terms:
        tkind = term.get("kind")
        if tkind == "const":
            val = term["value"]
            values.append(val)
            parts.append(term.get("label") or str(val))
        elif tkind == "percent_of":
            percent = term["percent"]
            field = term.get("of")
            base = context.get(field)
            if base is None:
                raise ValueError(f"formula needs input field: {field}")
            val = (percent / 100.0) * float(base)
            values.append(val)
            parts.append(f"{percent}% of {field}")
        else:
            raise ValueError(f"unsupported formula term kind: {tkind}")
    result = min(values)
    detail = "min(" + ", ".join(parts) + ") = " + str(_format_inr(result))
    return result, detail


def _format_inr(value: float) -> str:
    r = round(float(value), 2)
    return f"{r:,.0f}" if float(r).is_integer() else f"{r:,.2f}"


def active_scheme_scope(
    scope: dict[str, Any],
    all_scheme_ids: list[str],
    group_scheme_ids: dict[str, list[str]],
) -> list[str]:
    """Resolve a rule's scope object into concrete scheme ids (M2 §8).

    EXTERNAL_DOMAIN scopes are intentionally excluded from loan eligibility
    (DQ-007) and produce an empty scheme list here.
    """
    stype = scope.get("type")
    if stype == "ALL_CORE_SCHEMES":
        return list(all_scheme_ids)
    if stype == "SCHEME_LIST":
        return [sid for sid in (scope.get("schemes") or []) if sid in all_scheme_ids]
    if stype == "SCHEME_GROUP":
        group = scope.get("scheme_group")
        if not group:
            return []
        return [sid for sid in group_scheme_ids.get(group, []) if sid in all_scheme_ids]
    if stype == "EXTERNAL_DOMAIN":
        return []
    return []