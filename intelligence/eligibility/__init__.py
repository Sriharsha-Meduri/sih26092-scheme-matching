"""Eligibility evaluation (M2 §8)."""

from intelligence.eligibility import operators
from intelligence.eligibility.evaluator import evaluate_scheme
from intelligence.eligibility.operators import SUPPORTED_OPERATORS, apply_operator
from intelligence.eligibility.rules import applicable_rules, combine, group_rules, or_combine

__all__ = [
    "evaluate_scheme",
    "apply_operator",
    "SUPPORTED_OPERATORS",
    "applicable_rules",
    "combine",
    "group_rules",
    "or_combine",
    "operators",
]