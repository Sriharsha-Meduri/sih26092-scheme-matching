"""Deterministic normalization of profile/requirement inputs.

Policy (M2 §7): normalization is transformation, never inference. We only map a
value to a canonical form when the mapping is supported by the KB or by simple
unit conversion. Unrecognised values are preserved raw and surfaced as UNKNOWN
on their dependent rules — never invented, never silently dropped.
"""

from intelligence.normalization import finance, profile, activity, education, requirement

__all__ = ["finance", "profile", "activity", "education", "requirement"]