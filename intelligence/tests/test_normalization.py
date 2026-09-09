"""Normalization + validation (M2 §6, §7, §21-A/C)."""

import pytest

from intelligence import ApplicantProfile, Requirement
from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import MatchStatus, Purpose
from intelligence.normalization.education import resolve_course
from intelligence.normalization.finance import parse_inr
from intelligence.normalization.profile import (
    normalize_community,
    normalize_entity_type,
    normalize_profile,
    validate_profile,
)
from intelligence.normalization.requirement import normalize_requirement, validate_requirement


# --------------------------------------------------------------- finance
class TestParseInr:
    @pytest.mark.parametrize("raw,expected", [
        ("500000", 500000),
        ("5,00,000", 500000),
        ("5 lakh", 500000),
        ("₹5,00,000", 500000),
        ("3.5 Lakh", 350000),
        ("1.40 lakh", 140000),
        ("50 crore", 500000000),
        (500000, 500000),
        (None, None),
    ])
    def test_parse(self, raw, expected):
        assert parse_inr(raw) == expected

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_inr("none")


# -------------------------------------------------------------- community
class TestCommunity:
    def test_sc_variants(self):
        for raw in ("Scheduled Caste (SC)", "SC", "s.c.", "scheduled caste"):
            assert normalize_community(raw, None) == ("Scheduled Caste (SC)", True)

    def test_non_sc(self):
        assert normalize_community("General (non-SC)", None) == ("General (non-SC)", False)

    def test_is_sc_boolean(self):
        assert normalize_community(None, True) == ("Scheduled Caste (SC)", True)
        assert normalize_community(None, False) == ("General (non-SC)", False)

    def test_unrecognised_passthrough(self):
        assert normalize_community("OBC", None) == ("OBC", None)


class TestEntityType:
    @pytest.mark.parametrize("raw,expected", [
        ("Individual", "Individual"),
        ("individual", "Individual"),
        ("Sole Proprietor", "Individual"),
        ("Partnership Firm", "Partnership Firm"),
        ("Co-operative Society", "Co-operative Society"),
        ("coop", "Co-operative Society"),
    ])
    def test_aliases(self, raw, expected):
        assert normalize_entity_type(raw) == expected

    def test_unrecognised_passthrough(self):
        assert normalize_entity_type("LLP") == "LLP"


# --------------------------------------------------------------- profile
class TestValidateProfile:
    def test_non_boolean_certificate(self):
        with pytest.raises(ValueError):
            validate_profile(ApplicantProfile(caste_certificate="yes"))

    def test_negative_age(self):
        with pytest.raises(ValueError):
            validate_profile(ApplicantProfile(age=-1))

    def test_invalid_income_str(self):
        with pytest.raises(ValueError):
            validate_profile(ApplicantProfile(annual_family_income="NaN lakh"))

    def test_normalize_string_income(self):
        p = normalize_profile(ApplicantProfile(annual_family_income="3.5 lakh"))
        assert p.annual_family_income == 350000


# --------------------------------------------------------------- education resolution
class TestCourseResolution:
    def test_covered_family_by_name(self):
        kb = KnowledgeBase()
        res = resolve_course(None, "Engineering", kb)
        assert res.status is MatchStatus.MATCH
        assert res.coverage_status == "LISTED_IN_COVERED_COURSES"

    def test_non_covered_family(self):
        kb = KnowledgeBase()
        res = resolve_course(None, "Astrology", kb)
        assert res.status is MatchStatus.NO_MATCH

    def test_unresolvable_raw_course_unknown(self):
        kb = KnowledgeBase()
        res = resolve_course("Intro to Magic", None, kb)
        assert res.status is MatchStatus.UNKNOWN

    def test_missing(self):
        kb = KnowledgeBase()
        res = resolve_course(None, None, kb)
        assert res.status is MatchStatus.UNKNOWN
        assert res.matched_family_id is None


# --------------------------------------------------------------- requirement purpose
class TestPurpose:
    def test_business_when_activity(self):
        kb = KnowledgeBase()
        assert normalize_requirement(Requirement(activity="Tailoring"), kb).purpose is Purpose.BUSINESS

    def test_education_when_course_only(self):
        kb = KnowledgeBase()
        assert normalize_requirement(Requirement(course="B.Tech"), kb).purpose is Purpose.EDUCATION

    def test_unknown_when_neither(self):
        kb = KnowledgeBase()
        assert normalize_requirement(Requirement(), kb).purpose is Purpose.UNKNOWN

    def test_explicit_education_wins(self):
        kb = KnowledgeBase()
        req = Requirement(purpose="education", activity="Tailoring")
        assert normalize_requirement(req, kb).purpose is Purpose.EDUCATION

    def test_activity_not_resolved_for_education(self):
        kb = KnowledgeBase()
        req = Requirement(purpose="education", course="B.Tech", activity="")
        norm = normalize_requirement(req, kb)
        assert norm.purpose is Purpose.EDUCATION
        assert norm.activity_raw in (None, "")
        assert norm.activity.resolved is False


class TestValidateRequirement:
    def test_invalid_course_duration(self):
        with pytest.raises(ValueError):
            validate_requirement(Requirement(course_duration_years="soon"))


# --------------------------------------------------------------- activity resolution
class TestActivityResolution:
    def test_resolves_tailoring(self):
        from intelligence.normalization.activity import resolve_activity
        kb = KnowledgeBase()
        res = resolve_activity("Tailoring", kb)
        assert res.resolved is True
        assert res.canonical_activity_name == "Tailoring"

    def test_unresolved_kept_raw(self):
        from intelligence.normalization.activity import resolve_activity
        kb = KnowledgeBase()
        res = resolve_activity("Cinema Hall", kb)
        assert res.resolved is False
        assert res.raw == "Cinema Hall"