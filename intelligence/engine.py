"""RecommendationEngine — deterministic orchestrator (M2 §2, §3).

Pipeline (all steps deterministic, no LLM, no external calls):
  validate + normalize profile & requirement
    -> purpose-based candidate discovery
    -> per-candidate: eligibility (rules) | activity match | financial fit
       | education fit (ELS) | partner availability
    -> early-gate: business purpose with an activity not in the M1 taxonomy
       => overall UNSUPPORTED_ACTIVITY, no recommendations (G007)
    -> factor scoring (40/25/20/15) + deterministic ranking/tie-break
    -> explanation (reasons, warnings, source refs) + missing-field gaps

Everything the UI needs to explain a decision is present in the response:
reason keys (i18n), sources, rule results, factor breakdown, gaps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from intelligence.explanations.generator import attach_to_recommendation
from intelligence.gaps.detector import aggregate_missing_fields, detect_missing_fields
from intelligence.kb.repository import KnowledgeBase
from intelligence.eligibility.evaluator import evaluate_scheme
from intelligence.matching.activity import match_activity
from intelligence.matching.education import match_education
from intelligence.matching.financial import finance_fit
from intelligence.matching.partner import partner_fit
from intelligence.models.enums import (
    INCOME_GENERATING_SCHEMES,
    OverallStatus,
    Purpose,
    VerificationStatus,
    Verdict,
)
from intelligence.models.profile import ApplicantProfile
from intelligence.models.requirement import Location, RecommendationRequest, Requirement
from intelligence.models.result import (
    ActivityMatchResult,
    EligibilityResult,
    EngineMetadata,
    RecommendationResponse,
    RequestSummary,
    SchemeRecommendation,
)
from intelligence.normalization.profile import NormalizedProfile, normalize_profile, validate_profile
from intelligence.normalization.requirement import NormalizedRequirement, normalize_requirement, validate_requirement
from intelligence.ranking.ranking import rank_schemes
from intelligence.ranking.scorer import score_factors
from intelligence.explanations import reason_keys as RK


class RecommendationEngine:
    def __init__(self, kb_dir: Optional[str | Path] = None) -> None:
        self._kb = KnowledgeBase(Path(kb_dir) if kb_dir else None)

    @property
    def kb(self) -> KnowledgeBase:
        return self._kb

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        return self._recommend(request)

    # convenience: call directly with the flat inputs
    def evaluate(
        self,
        profile: Optional[ApplicantProfile] = None,
        requirement: Optional[Requirement] = None,
        location: Optional[Location] = None,
    ) -> RecommendationResponse:
        return self._recommend(
            RecommendationRequest(
                profile=profile or ApplicantProfile(),
                requirement=requirement or Requirement(),
                location=location,
            )
        )

    # ------------------------------------------------------------------ impl
    def _recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        if not isinstance(request, RecommendationRequest):
            raise TypeError("request must be a RecommendationRequest")

        validate_profile(request.profile)
        validate_requirement(request.requirement)

        norm_profile = normalize_profile(request.profile)
        norm_req = normalize_requirement(request.requirement, self._kb)

        # ---- candidate discovery (deterministic by purpose) -----------------
        purpose = norm_req.purpose
        candidates = self._candidate_schemes(purpose)

        # ---- early gate: activity provided but not in the taxonomy (G007) ---
        if purpose is Purpose.BUSINESS and norm_req.activity_raw and not norm_req.activity.resolved:
            return self._unsupported_activity(norm_profile, norm_req)

        summary = self._build_summary(norm_profile, norm_req)

        # ---- per-candidate evaluation --------------------------------------
        context = {
            "community": norm_profile.community,
            "annual_family_income": norm_profile.annual_family_income,
            "caste_certificate": norm_profile.caste_certificate,
            "entity_type": norm_profile.entity_type,
        }

        results: list[tuple[str, SchemeRecommendation]] = []
        for sid in candidates:
            rec = self._evaluate_candidate(sid, norm_profile, norm_req, context, purpose)
            results.append((sid, rec))

        # ---- scoring + ranking (deterministic ties) ------------------------
        scored = []
        for sid, rec in results:
            breakdown = score_factors(
                rec.eligibility, rec.activity_match, rec.financial_fit,
                rec.education_fit, rec.partner_fit,
            )
            rec.score = breakdown.total
            rec.factor_scores = breakdown.factor_scores
            scored.append((sid, rec))

        ranked = rank_schemes([(sid, rec.score, _breakdown_of(rec)) for sid, rec in scored])
        ranking = dict(ranked)
        for sid, rec in scored:
            rec.rank = ranking[sid]

        # ---- explanations + gaps ------------------------------------------
        for sid, rec in scored:
            rec.missing_fields = [
                f for f, _ in detect_missing_fields(
                    rec.eligibility, rec.activity_match, rec.financial_fit, rec.education_fit
                ).items()
            ]
            rec.verification_status = self._verification(rec.eligibility, rec.activity_match)
            attach_to_recommendation(self._kb, rec, purpose)

        recommendations = [rec for _, rec in sorted(scored, key=lambda x: x[1].rank)]

        missing_information = aggregate_missing_fields(recommendations, [])

        overall = self._overall_status(purpose, recommendations, norm_req)

        return RecommendationResponse(
            overall_status=overall,
            recommendations=recommendations,
            excluded_schemes=[],
            missing_information=missing_information,
            request_summary=summary,
            engine_metadata=self._metadata(),
        )

    # ------------------------------------------------------------- helpers
    def _candidate_schemes(self, purpose: Purpose) -> list[str]:
        if purpose is Purpose.EDUCATION:
            return ["NSFDC-ELS"]
        if purpose is Purpose.BUSINESS:
            return list(INCOME_GENERATING_SCHEMES)
        return []

    def _evaluate_candidate(
        self,
        sid: str,
        profile: NormalizedProfile,
        req: NormalizedRequirement,
        context: dict,
        purpose: Purpose,
    ) -> SchemeRecommendation:
        eligibility = evaluate_scheme(self._kb, sid, context)
        activity = match_activity(self._kb, sid, req.activity, purpose)
        financial = finance_fit(self._kb, sid, req, profile)
        education = match_education(self._kb, req, sid)
        partner = partner_fit(self._kb, sid)

        return SchemeRecommendation(
            scheme_id=sid,
            scheme_name=self._kb.scheme_name(sid),
            eligibility=eligibility,
            activity_match=activity,
            financial_fit=financial,
            education_fit=education,
            partner_fit=partner,
        )

    def _unsupported_activity(
        self, profile: NormalizedProfile, req: NormalizedRequirement
    ) -> RecommendationResponse:
        return RecommendationResponse(
            overall_status=OverallStatus.UNSUPPORTED_ACTIVITY,
            recommendations=[],
            request_summary=self._build_summary(profile, req),
            engine_metadata=self._metadata(),
        )

    def _verification(
        self, eligibility: EligibilityResult, activity: ActivityMatchResult
    ) -> VerificationStatus:
        if eligibility.verification is VerificationStatus.UNVERIFIED:
            return VerificationStatus.UNVERIFIED
        if activity.verification is VerificationStatus.UNVERIFIED:
            return VerificationStatus.UNVERIFIED
        return VerificationStatus.VERIFIED

    def _overall_status(
        self,
        purpose: Purpose,
        recommendations: list[SchemeRecommendation],
        req: NormalizedRequirement,
    ) -> OverallStatus:
        if purpose is Purpose.UNKNOWN:
            return OverallStatus.INSUFFICIENT_INFORMATION

        has_pass = False
        has_unknown = False
        for rec in recommendations:
            bucket = _oracle_bucket(rec)
            if bucket == "PASS":
                has_pass = True
            elif bucket == "UNKNOWN":
                has_unknown = True

        if has_pass:
            return OverallStatus.MATCHED
        if has_unknown:
            return OverallStatus.INSUFFICIENT_INFORMATION
        return OverallStatus.NO_MATCH

    def _build_summary(
        self, profile: NormalizedProfile, req: NormalizedRequirement
    ) -> RequestSummary:
        return RequestSummary(
            purpose=req.purpose.value if req.purpose else None,
            is_sc=profile.is_sc,
            community=profile.community,
            annual_family_income=profile.annual_family_income,
            entity_type=profile.entity_type,
            activity=req.activity_raw,
            project_cost=req.project_cost,
            requested_loan_amount=req.requested_loan_amount,
            course=req.course,
            course_family=req.course_family,
            course_fee=req.education_fee,
            state=None,
            district=None,
        )

    def _metadata(self) -> EngineMetadata:
        return EngineMetadata(
            kb_version=self._kb.kb_version,
            kb_schema_version=self._kb.schema_version,
            kb_generated_on=self._kb.generated_on,
            deterministic=True,
            llm_used=False,
        )


def _oracle_bucket(rec: SchemeRecommendation) -> str:
    """Map a candidate to PASS/UNKNOWN/FAIL exactly like the M1 golden oracle.

    income: eligibility PASS + financial PASS -> PASS; any FAIL -> FAIL; else UNKNOWN.
    Else   : ELS additionally requires the course-coverage (education) MATCH.
    """
    elig = rec.eligibility.verdict
    fin = rec.financial_fit.status
    edu = rec.education_fit.status

    if any(v is Verdict.FAIL for v in (elig, fin)):
        return "FAIL"
    if rec.scheme_id == "NSFDC-ELS":
        if elig is Verdict.PASS and fin is Verdict.PASS and edu.value == "MATCH":
            return "PASS"
        if any(v is Verdict.UNKNOWN for v in (elig, fin)) or edu.value == "UNKNOWN":
            return "UNKNOWN"
        return "FAIL"
    if elig is Verdict.PASS and fin is Verdict.PASS:
        return "PASS"
    return "UNKNOWN"


def _breakdown_of(rec: SchemeRecommendation):
    from intelligence.ranking.scorer import FactorBreakdown
    return FactorBreakdown(factor_scores=rec.factor_scores)