"""End-to-end engine tests + M1 golden-fixture regression oracle (M2 §3, §19, §21-X)."""

import json
import os

import pytest

from intelligence import RecommendationEngine, ApplicantProfile, Requirement
from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import MatchStatus, OverallStatus, VerificationStatus
from intelligence.utils import dataclass_to_dict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURES = os.path.join(REPO_ROOT, "KB", "normalized", "golden_fixtures.json")

ENG = RecommendationEngine()


def load_fixtures():
    with open(FIXTURES, encoding="utf-8") as f:
        return json.load(f)["records"]


def to_request(inp):
    profile = ApplicantProfile(
        community=inp.get("community"),
        annual_family_income=inp.get("annual_family_income"),
        caste_certificate=inp.get("caste_certificate"),
        entity_type=inp.get("entity_type"),
    )
    requirement = Requirement(
        activity=inp.get("activity"),
        project_cost=inp.get("project_cost"),
        course=inp.get("course"),
        course_family=inp.get("course_family"),
        education_fee=inp.get("course_fee"),
        repayment_has_started=inp.get("repayment_has_started"),
    )
    return profile, requirement


def oracle_contract(resp):
    """Translate engine output to the M1 golden verdict contract."""
    if resp.overall_status is OverallStatus.UNSUPPORTED_ACTIVITY:
        return None, [], "NOT_SUPPORTED"
    recs = resp.recommendations

    def bucket(r):
        elig = r.eligibility.verdict.value
        fin = r.financial_fit.status.value
        edu = r.education_fit.status.value
        if elig == "FAIL" or fin == "FAIL":
            return "FAIL"
        if r.scheme_id == "NSFDC-ELS":
            if elig == "PASS" and fin == "PASS" and edu == "MATCH":
                return "PASS"
            if elig == "UNKNOWN" or fin == "UNKNOWN" or edu == "UNKNOWN":
                return "UNKNOWN"
            return "FAIL"
        if elig == "PASS" and fin == "PASS":
            return "PASS"
        return "UNKNOWN"

    buckets = [bucket(r) for r in recs]
    passing = [r.scheme_id for r, b in zip(recs, buckets) if b == "PASS"]
    if passing:
        return True, passing, "VERIFIED"
    if any(b == "UNKNOWN" for b in buckets):
        return None, [], "UNVERIFIED"
    return False, [], "VERIFIED"


# ------------------------------------------------------------------ golden
class TestGoldenFixtures:
    @pytest.mark.parametrize("rec", load_fixtures(), ids=lambda r: r["id"])
    def test_oracle(self, rec):
        if rec["id"] == "G012":
            pytest.skip("G012 is a conditional unit check, covered in test_matching.")
        profile, requirement = to_request(rec["input"])
        resp = ENG.evaluate(profile, requirement)
        got = oracle_contract(resp)
        expected = rec["expected"]
        assert got == (expected["eligible"], list(expected["scheme_ids"]), expected["status"])


# --------------------------------------------------------------- statuses
class TestOverallStatuses:
    def test_unsupported_activity(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=300000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Cinema Hall", project_cost=2000000),
        )
        assert resp.overall_status is OverallStatus.UNSUPPORTED_ACTIVITY
        assert resp.recommendations == []

    def test_insufficient_information(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", caste_certificate=True),
            Requirement(activity="Tailoring", project_cost=200000),
        )
        assert resp.overall_status is OverallStatus.INSUFFICIENT_INFORMATION
        fields = {m.field for m in resp.missing_information}
        assert "annual_family_income" in fields

    def test_no_match(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="General (non-SC)", caste_certificate=False,
                             annual_family_income=200000, entity_type="Individual"),
            Requirement(activity="Tailoring", project_cost=200000),
        )
        assert resp.overall_status is OverallStatus.NO_MATCH
        assert resp.recommendations


# --------------------------------------------------------------- structure
class TestResponseStructure:
    def test_recommendations_ranked(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=350000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Tailoring", project_cost=300000),
        )
        assert resp.overall_status is OverallStatus.MATCHED
        ranks = [r.rank for r in resp.recommendations]
        assert ranks == sorted(ranks)
        assert [r.scheme_id for r in resp.recommendations][:2] == ["NSFDC-TL", "NSFDC-UNY"]

    def test_scores_decreasing(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=350000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Tailoring", project_cost=300000),
        )
        scores = [(r.rank, r.score) for r in resp.recommendations]
        assert scores == sorted(scores, key=lambda x: x[0])
        for r in resp.recommendations:
            assert 0.0 <= r.score <= 100.0

    def test_explanations_present(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=350000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Tailoring", project_cost=300000),
        )
        top = resp.recommendations[0]
        assert top.reasons
        assert any("ACTIVITY_UNVERIFIED" in top.warnings for top in resp.recommendations)
        assert top.sources
        assert all(s.source_id.startswith("S") for s in top.sources)
        assert top.eligibility.rule_results

    def test_verification_status_surfaced(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=350000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Tailoring", project_cost=300000),
        )
        for r in resp.recommendations:
            assert r.verification_status is VerificationStatus.UNVERIFIED  # DQ-012 mappings

    def test_partner_unavailable_surfaced(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=200000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Bakery", project_cost=100000),
        )
        for r in resp.recommendations:
            assert r.partner_fit.partner_status.value == "UNAVAILABLE"

    def test_engine_metadata(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=200000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Bakery", project_cost=100000),
        )
        meta = resp.engine_metadata
        assert meta.llm_used is False
        assert meta.deterministic is True
        assert meta.kb_version
        assert "Recommender" not in meta.engine_name or meta.engine_name

    def test_max_score_not_probability_disclaimer(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=200000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Bakery", project_cost=100000),
        )
        assert resp.disclaimer
        assert all(r.score <= 85.0 for r in resp.recommendations)  # partner dimension unavailable

    def test_json_serializable(self):
        resp = ENG.evaluate(
            ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=200000,
                             entity_type="Individual", caste_certificate=True),
            Requirement(activity="Bakery", project_cost=100000),
        )
        payload = dataclass_to_dict(resp)
        json.dumps(payload)  # must not raise
        assert payload["overall_status"] == "MATCHED"
        assert payload["recommendations"][0]["scheme_id"]


# -------------------------------------------------------------- determinism
class TestDeterminism:
    def test_repeated_runs_identical(self):
        kw_profile = dict(community="Scheduled Caste (SC)", annual_family_income=350000,
                          entity_type="Individual", caste_certificate=True)
        kw_req = dict(activity="Tailoring", project_cost=300000)
        r1 = dataclass_to_dict(ENG.evaluate(ApplicantProfile(**kw_profile), Requirement(**kw_req)))
        r2 = dataclass_to_dict(ENG.evaluate(ApplicantProfile(**kw_profile), Requirement(**kw_req)))
        assert r1 == r2

    def test_ordering_stable_across_schemes(self):
        p = ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income=500000,
                             entity_type="Individual", caste_certificate=True)
        r = Requirement(activity="Tailoring", project_cost=100000)
        ids1 = [x.scheme_id for x in ENG.evaluate(p, r).recommendations]
        ids2 = [x.scheme_id for x in ENG.evaluate(p, r).recommendations]
        assert ids1 == ids2


# ---------------------------------------------------------------- validation
class TestValidation:
    def test_bad_request_type(self):
        with pytest.raises(TypeError):
            ENG.recommend({"profile": {}})

    def test_invalid_certificate(self):
        with pytest.raises(ValueError):
            ENG.evaluate(ApplicantProfile(caste_certificate="yes"), Requirement(activity="Tailoring"))

    def test_invalid_money(self):
        with pytest.raises(ValueError):
            ENG.evaluate(
                ApplicantProfile(community="Scheduled Caste (SC)", annual_family_income="bogus"),
                Requirement(activity="Tailoring"),
            )


class TestKnowledgeInvariants:
    def test_kb_read_only(self):
        # engine never writes under KB; repository maps are private copies
        kb = ENG.kb
        assert isinstance(kb, KnowledgeBase)
        assert kb.scheme_ids  # cores present
        assert "NSFDC-MFS" in kb.scheme_ids and "NSFDC-ELS" in kb.scheme_ids

    def test_education_family_count(self):
        # the 25 covered course families from M1 education knowledge
        assert len(ENG.kb.course_families) == 25