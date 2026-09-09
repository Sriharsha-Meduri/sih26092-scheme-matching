"""Matching dimension implementations (activity / financial / education / partner)."""

from intelligence.matching.activity import match_activity
from intelligence.matching.education import match_education
from intelligence.matching.financial import finance_fit
from intelligence.matching.partner import partner_fit

__all__ = ["match_activity", "finance_fit", "match_education", "partner_fit"]