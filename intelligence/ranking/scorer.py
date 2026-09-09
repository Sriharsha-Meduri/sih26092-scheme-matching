"""Transparent factor scoring (M2 §9).

Rules (documented, deterministic, reproducibly computed):
- Frozen weights: eligibility 0.40, activity 0.25, financial 0.20, partner 0.15.
- A factor that does NOT apply to the case scores 100 (weight retained) and is
  reported as NOT_APPLICABLE so the frontend can render a breakdown.
- Partner data is unavailable in the current KB -> partner score 0 (weight
  retained), never fabricated, reported UNAVAILABLE.
- UNKNOWN factors score the neutral 50 (drives "needs more info", never FAIL).
- Total = sum(score_i * weight_i). Max achievable is 85 while partner data is
  unavailable. This is a MATCHING score, explicitly not a probability.

Factor state mapping:
  eligibility  Verdict  -> PASS:100  FAIL:0   UNKNOWN:50
  activity     MatchStatus -> MATCH(verified):100 MATCH(unverified):80
                             NO_MATCH:0  UNKNOWN:50  NOT_APPLICABLE:100
  financial    Verdict  -> PASS:100  FAIL:0   UNKNOWN:50
  partner      PartnerStatus -> UNAVAILABLE:0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from intelligence.models.enums import (
    Factor,
    MatchStatus,
    PartnerStatus,
    UNKNOWN_FACTOR_SCORE,
    UNVERIFIED_ACTIVITY_SCORE,
    VERIFIED_ACTIVITY_SCORE,
    VerificationStatus,
    Verdict,
)
from intelligence.models.result import (
    ActivityMatchResult,
    EducationFitResult,
    EligibilityResult,
    FactorScore,
    FinancialFitResult,
    PartnerFitResult,
)


@dataclass
class FactorBreakdown:
    factor_scores: list[FactorScore] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(fs.score * fs.weight for fs in self.factor_scores), 4)


def score_factors(
    eligibility: EligibilityResult,
    activity: ActivityMatchResult,
    financial: FinancialFitResult,
    education: EducationFitResult,
    partner: PartnerFitResult,
) -> FactorBreakdown:
    scores: list[FactorScore] = []

    # eligibility --------------------------------------------------------------
    elig_state, elig_score = _verdict_score(eligibility.verdict)
    scores.append(FactorScore(
        factor=Factor.ELIGIBILITY,
        state=elig_state,
        score=elig_score,
        weight=Factor.ELIGIBILITY.weight,
        detail=f"{len(eligibility.rule_results)} rule(s) evaluated",
    ))

    # activity -------------------------------------------------------------
    if activity.status is MatchStatus.NOT_APPLICABLE:
        act_state, act_score = "NOT_APPLICABLE", 100.0
    elif activity.status is MatchStatus.MATCH:
        if activity.verification is VerificationStatus.UNVERIFIED:
            act_state, act_score = "UNVERIFIED", float(UNVERIFIED_ACTIVITY_SCORE)
        else:
            act_state, act_score = "MATCH", float(VERIFIED_ACTIVITY_SCORE)
    elif activity.status is MatchStatus.NO_MATCH:
        act_state, act_score = "NO_MATCH", 0.0
    else:
        act_state, act_score = "UNKNOWN", float(UNKNOWN_FACTOR_SCORE)
    scores.append(FactorScore(
        factor=Factor.ACTIVITY,
        state=act_state,
        score=act_score,
        weight=Factor.ACTIVITY.weight,
        detail=activity.reason_key,
    ))

    # financial ------------------------------------------------------------
    fin_state, fin_score = _verdict_score(financial.status)
    scores.append(FactorScore(
        factor=Factor.FINANCIAL,
        state=fin_state,
        score=fin_score,
        weight=Factor.FINANCIAL.weight,
        detail=", ".join(financial.reason_keys) or financial.status.value,
    ))

    # education (informational; ELS only) -----------------------------------
    if education.status is MatchStatus.NOT_APPLICABLE:
        edu_state, edu_score = "NOT_APPLICABLE", 100.0
    elif education.status is MatchStatus.MATCH:
        edu_state, edu_score = "MATCH", 100.0
    elif education.status is MatchStatus.NO_MATCH:
        edu_state, edu_score = "NO_MATCH", 0.0
    else:
        edu_state, edu_score = "UNKNOWN", float(UNKNOWN_FACTOR_SCORE)
    # Education is folded into the eligibility stage for ELS; exposed but not weighted now.

    # partner --------------------------------------------------------------
    if partner.partner_status is PartnerStatus.UNAVAILABLE:
        par_state, par_score = "UNAVAILABLE", 0.0
    else:  # future real data path placeholder
        par_state, par_score = partner.status.value, float(partner.score)
    scores.append(FactorScore(
        factor=Factor.PARTNER_AVAILABILITY,
        state=par_state,
        score=par_score,
        weight=Factor.PARTNER_AVAILABILITY.weight,
        detail=partner.reason_key,
    ))

    return FactorBreakdown(factor_scores=scores)


def _verdict_score(verdict: Verdict) -> tuple[str, float]:
    if verdict is Verdict.PASS:
        return "PASS", 100.0
    if verdict is Verdict.FAIL:
        return "FAIL", 0.0
    if verdict is Verdict.NOT_APPLICABLE:
        return "NOT_APPLICABLE", 100.0
    return "UNKNOWN", float(UNKNOWN_FACTOR_SCORE)