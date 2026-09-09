"""Data-driven operator implementations (M2 §8).

The operator set mirrors the M1 eligibility_rule.schema.json enum:
  ==   !=   <   <=   >   >=   IN   NOT_IN   EXISTS   NO_CEILING

Each operator returns:
  True  -> rule PASS
  False -> rule FAIL
  None  -> rule UNKNOWN (the required actual value is missing; caller decides)

`apply_operator` never raises for the supported operator set and never guesses.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

OperatorFn = Callable[[Any, Any], Optional[bool]]


def _eq(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return actual == expected


def _ne(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return actual != expected


def _lt(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return actual < expected


def _le(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return actual <= expected


def _gt(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return actual > expected


def _ge(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return actual >= expected


def _in(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    values = expected if isinstance(expected, (list, tuple, set)) else [expected]
    return actual in values


def _not_in(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    values = expected if isinstance(expected, (list, tuple, set)) else [expected]
    return actual not in values


def _exists(expected: Any, actual: Any) -> Optional[bool]:
    if actual is None:
        return None
    return bool(actual)


def _no_ceiling(expected: Any, actual: Any) -> Optional[bool]:
    """NO_CEILING declares no constraint; the rule passes when evaluated
    (E007 is EXTERNAL_DOMAIN and is never applied to loan eligibility, so this
    is only reachable through an explicit scope override)."""
    return True


OPERATORS: dict[str, OperatorFn] = {
    "==": _eq,
    "!=": _ne,
    "<": _lt,
    "<=": _le,
    ">": _gt,
    ">=": _ge,
    "IN": _in,
    "NOT_IN": _not_in,
    "EXISTS": _exists,
    "NO_CEILING": _no_ceiling,
}

SUPPORTED_OPERATORS: frozenset[str] = frozenset(OPERATORS)


def apply_operator(operator: str, expected: Any, actual: Any) -> Optional[bool]:
    fn = OPERATORS.get(operator)
    if fn is None:
        raise ValueError(f"unsupported operator: {operator}")
    return fn(expected, actual)