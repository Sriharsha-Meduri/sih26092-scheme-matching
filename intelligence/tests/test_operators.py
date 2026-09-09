"""Operator semantics (M2 §8, §21-B).

Each operator: True -> PASS, False -> FAIL, None -> UNKNOWN (missing actual).
UNKNOWN must never be coerced into FAIL.
"""

import pytest

from intelligence.eligibility.operators import apply_operator


@pytest.mark.parametrize("op,expected,actual,result", [
    ("==", "Scheduled Caste (SC)", "Scheduled Caste (SC)", True),
    ("==", "Scheduled Caste (SC)", "General (non-SC)", False),
    ("==", "Scheduled Caste (SC)", None, None),
    ("!=", "A", "B", True),
    ("!=", "A", "A", False),
    ("<", 500000, 300000, True),
    ("<", 500000, 500000, False),
    ("<=", 500000, 500000, True),
    ("<=", 500000, 500001, False),
    (">", 140000, 140001, True),
    (">", 140000, 140000, False),
    (">=", 100, 100, True),
    ("IN", ["Individual", "Partnership Firm"], "Individual", True),
    ("IN", ["Individual"], "Co-operative Society", False),
    ("IN", "Individual", "Individual", True),
    ("NOT_IN", ["Construction"], "Plantation", True),
    ("NOT_IN", ["Plantation"], "Plantation", False),
    ("EXISTS", None, True, True),
    ("EXISTS", None, False, False),
    ("EXISTS", None, None, None),
    ("EXISTS", None, "cert-123", True),
    ("NO_CEILING", None, 900000, True),
    ("NO_CEILING", None, None, True),
])
def test_operator_truth_table(op, expected, actual, result):
    assert apply_operator(op, expected, actual) is result


def test_unsupported_operator_raises():
    with pytest.raises(ValueError):
        apply_operator("LIKE", "x", "y")