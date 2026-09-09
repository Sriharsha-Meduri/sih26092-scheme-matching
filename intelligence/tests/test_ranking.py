"""Scoring + ranking determinism (M2 §9, §19)."""

import pytest

from intelligence.kb.repository import KnowledgeBase
from intelligence.matching.activity import match_activity
from intelligence.matching.education import match_education
from intelligence.matching.financial import finance_fit
from intelligence.matching.partner import partner_fit
from intelligence.models.enums import (
    Factor,
    MatchStatus,
    PartnerStatus,
    Purpose,
    VerificationStatus,
    Verdict,
)
from intelligence.normalization.activity import ActivityResolution
from intelligence.normalization.profile import NormalizedProfile
from intelligence.normalization.requirement import NormalizedRequirement
from intelligence.ranking.ranking import rank_schemes
from intelligence.ranking.scorer import score_factors

KB = KnowledgeBase()


def breakdown(sid, *, elig=Verdict.PASS, activity="MATCH", act_verified=False,
              fin=Verdict.PASS, edu=MatchStatus.NOT_APPLICABLE, partner_unavail=True):
    from intelligence.models.result import (
        ActivityMatchResult, EducationFitResult, EligibilityResult,
        FinancialFitResult, PartnerFitResult,
    )
    eligibility = EligibilityResult(scheme_id=sid, verdict=elig)
    if activity == "MATCH":
        act = ActivityMatchResult(
            scheme_id=sid, status=MatchStatus.MATCH, reason_key="ACTIVITY_MATCH",
            verification=VerificationStatus.VERIFIED if act_verified else VerificationStatus.UNVERIFIED,
        )
    elif activity == "NO_MATCH":
        act = ActivityMatchResult(scheme_id=sid, status=MatchStatus.NO_MATCH, reason_key="ACTIVITY_NO_MATCH")
    elif activity == "NOT_APPLICABLE":
        act = ActivityMatchResult(scheme_id=sid, status=MatchStatus.NOT_APPLICABLE, reason_key="ACTIVITY_MATCH")
    else:
        act = ActivityMatchResult(scheme_id=sid, status=MatchStatus.UNKNOWN, reason_key="MISSING_ACTIVITY")
    edu_res = EducationFitResult(scheme_id=sid, status=edu, reason_key="COURSE_COVERED" if edu is MatchStatus.MATCH else "n/a")
    fin_res = FinancialFitResult(scheme_id=sid, status=fin)
    par_res = PartnerFitResult(scheme_id=sid, status=Verdict.UNKNOWN,
                               partner_status=PartnerStatus.UNAVAILABLE if partner_unavail else None,
                               score=0)
    return score_factors(eligibility, act, fin_res, edu_res, par_res)


class TestScoring:
    def test_full_pass(self):
        # eligibility 40 + activity 25 + financial 20 + partner 0 => 85
        # (85 is the ceiling while partner data is unavailable)
        b = breakdown("NSFDC-MFS", act_verified=True)
        assert b.total == pytest.approx(85.0)
        for fs in b.factor_scores:
            if fs.factor is Factor.PARTNER_AVAILABILITY:
                assert fs.score == 0.0

    def test_default_unverified_activity_total(self):
        b = breakdown("NSFDC-MFS")
        # unverified activity mapping (DQ-012) drops activity from 25 to 20
        assert b.total == pytest.approx(80.0)

    def test_not_applicable_factor_scores_100(self):
        b = breakdown("NSFDC-ELS", activity="NOT_APPLICABLE")
        act_fs = next(fs for fs in b.factor_scores if fs.factor is Factor.ACTIVITY)
        # ELS activity NOT_APPLICABLE scores 100, weight retained
        assert act_fs.state == "NOT_APPLICABLE"
        assert act_fs.score == 100.0

    def test_unverified_activity_reduces_score(self):
        b = breakdown("NSFDC-MFS", act_verified=False)
        act_fs = next(fs for fs in b.factor_scores if fs.factor is Factor.ACTIVITY)
        assert act_fs.score == 80.0

    def test_verified_activity_full(self):
        b = breakdown("NSFDC-MFS", act_verified=True)
        act_fs = next(fs for fs in b.factor_scores if fs.factor is Factor.ACTIVITY)
        assert act_fs.score == 100.0

    def test_unknown_factor_scores_50(self):
        b = breakdown("NSFDC-MFS", elig=Verdict.UNKNOWN)
        elig_fs = next(fs for fs in b.factor_scores if fs.factor is Factor.ELIGIBILITY)
        assert elig_fs.score == 50.0


class TestTieBreak:
    def _rank(self, items):
        return [sid for sid, _ in rank_schemes(items)]

    def test_score_desc_groups(self):
        from intelligence.models.result import FactorScore
        from intelligence.ranking.scorer import FactorBreakdown

        def bd(total):
            # single factor with weight 1.0 yields the requested total
            return FactorBreakdown(factor_scores=[
                FactorScore(factor=Factor.ELIGIBILITY, state="PASS", score=total, weight=1.0),
            ])

        items = [
            ("A", 80.0, bd(80.0)),
            ("B", 60.0, bd(60.0)),
        ]
        assert self._rank([("A", 80.0, bd(80.0)), ("B", 60.0, bd(60.0))]) == ["A", "B"]

    def test_tie_breaks_on_mfs_tl_amy_uny_priority(self):
        b_a = breakdown("NSFDC-AMY")
        b_m = breakdown("NSFDC-MFS")
        ranked = self._rank([("NSFDC-AMY", b_a.total, b_a), ("NSFDC-MFS", b_m.total, b_m)])
        # equal totals -> SCHEME_PRIORITY order puts MFS before AMY
        assert ranked == ["NSFDC-MFS", "NSFDC-AMY"]

    def test_no_randomness(self):
        b = breakdown("NSFDC-UNY")
        r1 = rank_schemes([("NSFDC-UNY", b.total, b), ("NSFDC-TL", b.total, b)])
        r2 = rank_schemes([("NSFDC-UNY", b.total, b), ("NSFDC-TL", b.total, b)])
        assert r1 == r2
        # exact tie keeps the same rank; priority orders TL before UNY
        assert [sid for sid, _ in r1] == ["NSFDC-TL", "NSFDC-UNY"]
        assert [rank for _, rank in r1] == [1, 1]