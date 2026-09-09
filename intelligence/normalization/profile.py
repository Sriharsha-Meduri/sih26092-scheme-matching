"""Profile normalization + validation (M2 §6, §21-A).

Builds a canonical, typed view of the applicant profile that the eligibility
engine can evaluate against the M1 rules, plus a record of what was normalized
(so the explanation layer can cite transforms transparently).

Rules for unknown/missing: every canonical field stays None when the input does
not provide it or provides an unrecognized value. None -> UNKNOWN downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from intelligence.models.profile import (
    ENTITY_TYPE_ALIASES,
    ENTITY_TYPE_VALUES,
    GENERAL_NON_SC,
    SC_COMMUNITY_CANONICAL,
    ApplicantProfile,
)
from intelligence.normalization.finance import parse_inr

Number = Union[int, float]


@dataclass
class NormalizedProfile:
    community: Optional[str] = None
    is_sc: Optional[bool] = None
    annual_family_income: Optional[Number] = None
    caste_certificate: Optional[bool] = None
    entity_type: Optional[str] = None
    education_status: Optional[str] = None
    employment_status: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    normalized_fields: set[str] = field(default_factory=set)


def normalize_community(community: Optional[str], is_sc: Optional[bool]) -> tuple[Optional[str], Optional[bool]]:
    """Map community/social-category / is_sc inputs to the canonical community string."""
    if community is not None:
        key = community.strip().lower()
        if "scheduled caste" in key or key in ("sc", "s.c.", "s.c", "schedule caste"):
            return SC_COMMUNITY_CANONICAL, True
        if key in ("general", "general (non-sc)", "non-sc", "non sc", "general other"):
            return GENERAL_NON_SC, False
        return community, None
    if is_sc is True:
        return SC_COMMUNITY_CANONICAL, True
    if is_sc is False:
        return GENERAL_NON_SC, False
    return None, None


def normalize_entity_type(value: Optional[str]) -> Optional[str]:
    if value is None or not str(value).strip():
        return None
    key = str(value).strip().lower()
    if key in ENTITY_TYPE_VALUES or key in ENTITY_TYPE_ALIASES:
        return ENTITY_TYPE_ALIASES.get(key, value)
    # case-insensitive tolerance of the canonical values
    for canon in ENTITY_TYPE_VALUES:
        if canon.lower() == key:
            return canon
    return value


def normalize_profile(profile: ApplicantProfile) -> NormalizedProfile:
    if not isinstance(profile, ApplicantProfile):
        raise TypeError("profile must be an ApplicantProfile")

    community, is_sc = normalize_community(profile.community, profile.is_sc)
    income = parse_inr(profile.annual_family_income)
    entity = normalize_entity_type(profile.entity_type)

    normalized = NormalizedProfile(
        community=community,
        is_sc=is_sc,
        annual_family_income=income,
        caste_certificate=profile.caste_certificate,
        entity_type=entity,
        education_status=profile.education_status,
        employment_status=profile.employment_status,
        age=profile.age,
        gender=profile.gender,
    )
    if profile.community is not None or profile.is_sc is not None:
        normalized.normalized_fields.add("community")
    if profile.annual_family_income is not None:
        normalized.normalized_fields.add("annual_family_income")
    if profile.entity_type is not None:
        normalized.normalized_fields.add("entity_type")
    return normalized


def validate_profile(profile: ApplicantProfile) -> None:
    """Early, hard validation of profile shape (M2 §21-A, M0 §8 input bounds)."""
    if profile.caste_certificate is not None and not isinstance(profile.caste_certificate, bool):
        raise ValueError("caste_certificate must be a boolean or None")
    if profile.is_sc is not None and not isinstance(profile.is_sc, bool):
        raise ValueError("is_sc must be a boolean or None")
    if profile.age is not None and not isinstance(profile.age, int):
        raise ValueError("age must be an integer or None")
    if profile.annual_family_income is not None:
        parse_inr(profile.annual_family_income)  # raises on invalid