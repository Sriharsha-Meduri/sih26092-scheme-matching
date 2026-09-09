"""Canonical applicant profile (intelligence input contract).

Field names mirror the M1 normalized KB rule fields where one exists:
  - community             -> E001 (== Scheduled Caste (SC))
  - annual_family_income  -> E002 (<= 500000 INR)
  - caste_certificate     -> E003 (EXISTS)
  - entity_type           -> E004/E005/E006 (IN Individual | Partnership Firm | Co-operative Society)

Values are typed but deliberately optional: a missing field means UNKNOWN for
the dependent rules, never a silent FAIL. `is_sc` is a back-end convenience
that maps to `community` during normalization (is_sc=True -> scheduled caste,
False -> General (non-SC)); `community` takes precedence when both are set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class ApplicantProfile:
    community: Optional[str] = None                                  # "Scheduled Caste (SC)" canonical form
    is_sc: Optional[bool] = None                                     # convenience boolean (normalized into community)
    annual_family_income: Optional[Union[int, float, str]] = None    # INR; strings like "3.5 lakh" normalized
    caste_certificate: Optional[bool] = None                         # True/False/None
    entity_type: Optional[str] = None                                # Individual | Partnership Firm | Co-operative Society
    education_status: Optional[str] = None                           # contextual (no KB rule currently consumes it)
    employment_status: Optional[str] = None                          # contextual
    age: Optional[int] = None                                        # contextual (not used by current rules)
    gender: Optional[str] = None                                     # contextual

    def __post_init__(self) -> None:
        if self.age is not None and self.age < 0:
            raise ValueError("age must be non-negative")


SC_COMMUNITY_CANONICAL = "Scheduled Caste (SC)"
GENERAL_NON_SC = "General (non-SC)"

ENTITY_TYPE_VALUES: tuple[str, ...] = (
    "Individual",
    "Partnership Firm",
    "Co-operative Society",
)

# Accepted aliases (normalization maps them to canonical entity types).
ENTITY_TYPE_ALIASES: dict[str, str] = {
    "individual": "Individual",
    "sole proprietor": "Individual",
    "partnership": "Partnership Firm",
    "partnership firm": "Partnership Firm",
    "partnershipfirm": "Partnership Firm",
    "cooperative": "Co-operative Society",
    "co-operative": "Co-operative Society",
    "cooperative society": "Co-operative Society",
    "co-operative society": "Co-operative Society",
    "coop": "Co-operative Society",
}