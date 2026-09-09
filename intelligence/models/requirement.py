"""Canonical requirement + location (intelligence input contract).

Requirement drives deterministic candidate discovery:
  - BUSINESS purpose   -> 4 income-generating schemes (MFS/TL/AMY/UNY)
  - EDUCATION purpose  -> ELS only

`activity` is raw user text (e.g. "tailoring shop"); the normalizer resolves it
to a canonical activity id when the M1 taxonomy contains a match. Monetary
inputs accept strings ("5 lakh", "5,00,000") and are normalized to INR numbers.
Conditional inputs (channel_type, activity_category, repayment_has_started,
course_duration_years) resolve M1 conditional financial values where the user
supplies them; otherwise those values are reported UNKNOWN, never inferred.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from intelligence.models.profile import ApplicantProfile


@dataclass
class Location:
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __post_init__(self) -> None:
        if self.latitude is not None and not (-90.0 <= float(self.latitude) <= 90.0):
            raise ValueError("latitude out of bounds [-90, 90]")
        if self.longitude is not None and not (-180.0 <= float(self.longitude) <= 180.0):
            raise ValueError("longitude out of bounds [-180, 180]")


@dataclass
class Requirement:
    purpose: Optional[str] = None                 # "business" | "education" (unknown when omitted)
    requirement_type: Optional[str] = None        # contextual
    activity: Optional[str] = None                # raw user activity text
    project_cost: Optional[Union[int, float, str]] = None   # INR
    requested_loan_amount: Optional[Union[int, float, str]] = None  # INR
    course: Optional[str] = None                  # raw course text, e.g. "B.Tech"
    course_family: Optional[str] = None           # canonical/raw course family, e.g. "Engineering"
    education_fee: Optional[Union[int, float, str]] = None    # INR
    course_duration_years: Optional[Union[int, float]] = None  # ELS moratorium (M0 B7); optional
    institution_type: Optional[str] = None        # contextual (no KB data yet)
    channel_type: Optional[str] = None            # UNY rate / channel info, e.g. "Small Finance Banks (SFBs)"
    activity_category: Optional[str] = None       # TL moratorium: "Plantation" | "Construction"
    repayment_has_started: Optional[bool] = None  # ELS repayment/moratorium branch
    location: Optional[Location] = None


@dataclass
class RecommendationRequest:
    profile: ApplicantProfile = field(default_factory=ApplicantProfile)
    requirement: Requirement = field(default_factory=Requirement)
    location: Optional[Location] = None