"""Deterministic ranking + tie-breaking (M2 §9, §19).

Sort order:
  1. score descending
  2. eligibility factor score descending
  3. financial factor score descending
  4. activity factor score descending
  5. KB scheme_file order (SCHEME_PRIORITY)

No randomness, no time dependence. Same inputs -> identical ordering.
"""

from __future__ import annotations

from intelligence.models.enums import SCHEME_PRIORITY
from intelligence.ranking.scorer import FactorBreakdown


def _factor_score(breakdown: FactorBreakdown, factor_name: str) -> float:
    for fs in breakdown.factor_scores:
        if fs.factor.value == factor_name:
            return fs.score
    return 0.0


def rank_schemes(items: list[tuple[str, float, FactorBreakdown]]) -> list[tuple[str, int]]:
    """items: [(scheme_id, total, breakdown)] -> sorted [(scheme_id, rank)]."""
    priority = {sid: i for i, sid in enumerate(SCHEME_PRIORITY)}

    def sort_key(item):
        scheme_id, total, breakdown = item
        return (
            -total,
            -_factor_score(breakdown, "eligibility"),
            -_factor_score(breakdown, "financial"),
            -_factor_score(breakdown, "activity"),
            priority.get(scheme_id, 10 ** 9),
            scheme_id,
        )

    ordered = sorted(items, key=sort_key)
    # rank may tie intentionally: same score/subscores -> same rank
    ranks: list[tuple[str, int]] = []
    designed = {}
    for position, (scheme_id, total, breakdown) in enumerate(ordered, start=1):
        if position == 1:
            designed[scheme_id] = 1
        else:
            prev_id, prev = ordered[position - 2][0], ordered[position - 2]
            if (total, _factor_score(breakdown, "eligibility"),
                    _factor_score(breakdown, "financial"),
                    _factor_score(breakdown, "activity")) == (
                prev[1], _factor_score(prev[2], "eligibility"),
                _factor_score(prev[2], "financial"),
                _factor_score(prev[2], "activity")):
                designed[scheme_id] = designed[prev_id]
            else:
                designed[scheme_id] = position
    for scheme_id, total, breakdown in ordered:
        ranks.append((scheme_id, designed[scheme_id]))
    return ranks