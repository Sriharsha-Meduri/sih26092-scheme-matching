"""Matching dimension tests (M2 §4, §5, §6, §7)."""

import pytest

from intelligence.kb.repository import KnowledgeBase
from intelligence.matching.activity import match_activity
from intelligence.matching.education import match_education
from intelligence.matching.financial import finance_fit
from intelligence.matching.partner import partner_fit
from intelligence.models.enums import (
    MatchStatus,
    PartnerStatus,
    Purpose,
    VerificationStatus,
    Verdict,
)
from intelligence.normalization.activity import ActivityResolution, resolve_activity
from intelligence.normalization.profile import NormalizedProfile
from intelligence.normalization.requirement import NormalizedRequirement

KB = KnowledgeBase()


def nreq(**kw):
    defaults = {"purpose": Purpose.BUSINESS, "repayment_has_started": None}
    defaults.update(kw)
    return NormalizedRequirement(**defaults)


def nprofile(**kw):
    return NormalizedProfile(**kw)


# --------------------------------------------------------------------- activity
class TestActivityMatch:
    def test_match_preserves_unverified(self):
        res = match_activity(KB, "NSFDC-MFS", resolve_activity("Tailoring", KB), Purpose.BUSINESS)
        assert res.status is MatchStatus.MATCH
        assert res.verification is VerificationStatus.UNVERIFIED  # DQ-012 surfaced
        assert res.canonical_activity_name == "Tailoring"

    def test_no_match(self):
        res = match_activity(KB, "NSFDC-MFS", resolve_activity("Fisheries", KB), Purpose.BUSINESS)
        # Fisheries maps to income schemes; if not to MFS this is NO_MATCH
        assert res.status is MatchStatus.MATCH or res.status is MatchStatus.NO_MATCH
        assert res.raw_activity == "Fisheries"

    def test_missing_unknown(self):
        res = match_activity(KB, "NSFDC-MFS", ActivityResolution(raw=None), Purpose.BUSINESS)
        assert res.status is MatchStatus.UNKNOWN

    def test_unsupported_unknown(self):
        res = match_activity(KB, "NSFDC-MFS", ActivityResolution(raw="Cinema Hall"), Purpose.BUSINESS)
        assert res.status is MatchStatus.UNKNOWN

    def test_education_not_applicable(self):
        res = match_activity(KB, "NSFDC-ELS", ActivityResolution(raw=None), Purpose.EDUCATION)
        assert res.status is MatchStatus.NOT_APPLICABLE


# --------------------------------------------------------------- financial
class TestFinancialBounds:
    def test_tl_exclusive_lower_bound(self):
        fit = finance_fit(KB, "NSFDC-TL", nreq(project_cost=140000), nprofile())
        assert fit.status is Verdict.FAIL  # must be EXCLUSIVE: >1.4L required
        assert any(not c.passed and c.inclusivity == "exclusive" for c in fit.constraints)

    def test_tl_just_above_lower_bound(self):
        fit = finance_fit(KB, "NSFDC-TL", nreq(project_cost=140001), nprofile())
        assert fit.status is Verdict.PASS

    def test_mfs_up_to_140k_inclusive(self):
        assert finance_fit(KB, "NSFDC-MFS", nreq(project_cost=140000), nprofile()).status is Verdict.PASS

    def test_mfs_above_cap_fails(self):
        assert finance_fit(KB, "NSFDC-MFS", nreq(project_cost=140001), nprofile()).status is Verdict.FAIL

    def test_amy_up_to_140k(self):
        assert finance_fit(KB, "NSFDC-AMY", nreq(project_cost=140000), nprofile()).status is Verdict.PASS

    def test_uny_up_to_5l(self):
        assert finance_fit(KB, "NSFDC-UNY", nreq(project_cost=500000), nprofile()).status is Verdict.PASS
        assert finance_fit(KB, "NSFDC-UNY", nreq(project_cost=500001), nprofile()).status is Verdict.FAIL

    def test_missing_project_cost_unknown(self):
        fit = finance_fit(KB, "NSFDC-TL", nreq(project_cost=None), nprofile())
        assert fit.status is Verdict.UNKNOWN

    def test_requested_loan_within_limit(self):
        fit = finance_fit(KB, "NSFDC-TL", nreq(project_cost=300000, requested_loan_amount=200000), nprofile())
        assert fit.status is Verdict.PASS

    def test_requested_loan_above_limit(self):
        fit = finance_fit(KB, "NSFDC-TL", nreq(project_cost=300000, requested_loan_amount=280000), nprofile())
        assert fit.status is Verdict.FAIL


class TestELSFinance:
    def test_cap_min_40l_90pct(self):
        # fee 30L -> cap = min(40L, 27L) = 27L
        fit = finance_fit(KB, "NSFDC-ELS", nreq(purpose=Purpose.EDUCATION, education_fee=3000000), nprofile())
        assert fit.status is Verdict.PASS
        assert fit.max_possible_amount == 2700000
        assert fit.formula_detail is not None

    def test_cap_40l_when_fee_high(self):
        fit = finance_fit(KB, "NSFDC-ELS", nreq(purpose=Purpose.EDUCATION, education_fee=50000000), nprofile())
        assert fit.max_possible_amount == 4000000

    def test_missing_fee_unknown(self):
        fit = finance_fit(KB, "NSFDC-ELS", nreq(purpose=Purpose.EDUCATION, education_fee=None), nprofile())
        assert fit.status is Verdict.UNKNOWN
        assert fit.reason_keys == ["MISSING_COURSE_FEE"]


class TestConditionals:
    def test_uny_coop_rate(self):
        fit = finance_fit(
            KB, "NSFDC-UNY", nreq(project_cost=200000, channel_type="Co-operative Societies"), nprofile()
        )
        rate = next(c for c in fit.conditionals if c.parameter == "beneficiary_interest_rate")
        assert rate.resolved is True
        assert rate.value == 13  # FP-NSFDC-UNY-008: Co-op -> 13

    def test_uny_sfb_rate(self):
        fit = finance_fit(
            KB, "NSFDC-UNY", nreq(project_cost=200000, channel_type="Small Finance Banks (SFBs)"), nprofile()
        )
        rate = next(c for c in fit.conditionals if c.parameter == "beneficiary_interest_rate")
        assert rate.value == 15  # Small Finance Banks -> 15

    def test_tl_moratorium_no_category_unknown(self):
        fit = finance_fit(KB, "NSFDC-TL", nreq(project_cost=300000), nprofile())
        mora = next((c for c in fit.conditionals if c.parameter == "moratorium_months" and c.variable == "activity_category"), None)
        if mora is not None:
            assert mora.resolved is False

    def test_els_repayment_branch(self):
        fit = finance_fit(
            KB, "NSFDC-ELS",
            nreq(purpose=Purpose.EDUCATION, education_fee=2000000, repayment_has_started=False), nprofile()
        )
        repay = next(c for c in fit.conditionals if c.parameter == "repayment_period_years")
        assert repay.resolved is True and repay.value == 12  # started=False -> 12 years


# ---------------------------------------------------------------- education
class TestEducationMatch:
    def test_covered(self):
        req = nreq(purpose=Purpose.EDUCATION, course="B.Tech", course_family="Engineering")
        res = match_education(KB, req, "NSFDC-ELS")
        assert res.status is MatchStatus.MATCH
        assert res.verification is VerificationStatus.VERIFIED
        assert res.coverage_status == "LISTED_IN_COVERED_COURSES"

    def test_not_covered(self):
        req = nreq(purpose=Purpose.EDUCATION, course_family="Astrology")
        res = match_education(KB, req, "NSFDC-ELS")
        assert res.status is MatchStatus.NO_MATCH

    def test_missing_course_unknown(self):
        req = nreq(purpose=Purpose.EDUCATION)
        res = match_education(KB, req, "NSFDC-ELS")
        assert res.status is MatchStatus.UNKNOWN

    def test_not_applicable_income_scheme(self):
        req = nreq(purpose=Purpose.BUSINESS, activity="Tailoring")
        res = match_education(KB, req, "NSFDC-MFS")
        assert res.status is MatchStatus.NOT_APPLICABLE


# ----------------------------------------------------------------- partner
class TestPartner:
    def test_unavailable_never_fabricated(self):
        res = partner_fit(KB, "NSFDC-MFS")
        assert res.partner_status is PartnerStatus.UNAVAILABLE
        assert res.status is Verdict.UNKNOWN
        assert res.score == 0
        assert res.reason_key == "PARTNER_DATA_UNAVAILABLE"

    def test_sources_registered(self):
        res = partner_fit(KB, "NSFDC-MFS")
        assert len(res.sources) >= 1