from app.intelligence.engine import EngineRecommendation, EngineResult, get_engine
from app.main import app
from tests.conftest import BUSINESS_PROFILE, EDUCATION_PROFILE


def test_missing_required_field_is_422(client):
    body = dict(BUSINESS_PROFILE)
    body.pop("is_sc")
    res = client.post("/api/recommend", json=body)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_negative_income_is_422(client):
    res = client.post("/api/recommend", json={**BUSINESS_PROFILE, "annual_income": -1})
    assert res.status_code == 422


def test_invalid_purpose_is_422(client):
    res = client.post("/api/recommend", json={**BUSINESS_PROFILE, "purpose": "holiday"})
    assert res.status_code == 422


def test_invalid_location_is_422(client):
    res = client.post("/api/recommend", json={**BUSINESS_PROFILE, "location": {"lat": 95, "lng": 0}})
    assert res.status_code == 422


def test_business_profile_ranks_business_schemes_first(client):
    res = client.post("/api/recommend", json=BUSINESS_PROFILE)
    assert res.status_code == 200
    body = res.json()
    assert body["engine"]["name"] == "mock"
    assert body["engine"]["is_prototype"] is True
    assert "not a government approval" in body["disclaimer"]

    recs = body["recommendations"]
    assert len(recs) == 5
    top = recs[0]
    assert top["eligible"] is True
    assert top["scheme"]["max_loan_amount"] is not None
    assert top["source_type"] == "prototype_mock"
    assert all(r.startswith("Prototype engine") for r in top["reasons"])

    by_id = {r["scheme_id"]: r for r in recs}
    assert by_id["NSFDC-ELS"]["eligible"] is False  # education scheme for a business purpose
    assert by_id["NSFDC-MFS"]["eligible"] is False  # project cost above its stored limit
    assert by_id["NSFDC-TL"]["eligible"] is True

    # eligible ones first, then by score
    eligible_flags = [r["eligible"] for r in recs]
    assert eligible_flags == sorted(eligible_flags, reverse=True)


def test_education_profile_ranks_education_scheme_first(client):
    res = client.post("/api/recommend", json=EDUCATION_PROFILE)
    assert res.status_code == 200
    recs = res.json()["recommendations"]
    assert recs[0]["scheme_id"] == "NSFDC-ELS"
    assert recs[0]["eligible"] is True


class FakeEngine:
    """Stands in for Developer 1's engine to prove the adapter boundary works."""

    name = "fake-real-engine"
    is_prototype = False

    def recommend(self, profile, schemes):
        return EngineResult(
            recommendations=[
                EngineRecommendation(scheme_id="NSFDC-TL", scheme_name="Term Loan", eligible=True, score=94,
                                     reasons=["Income within applicable limit", "Activity is eligible"]),
                EngineRecommendation(scheme_id="UNKNOWN-X", scheme_name="Mystery", eligible=False, score=0,
                                     reasons=["Not in the scheme master"]),
            ]
        )


def test_engine_adapter_is_pluggable_and_enriched(client):
    app.dependency_overrides[get_engine] = lambda: FakeEngine()
    try:
        res = client.post("/api/recommend", json=BUSINESS_PROFILE)
    finally:
        app.dependency_overrides.pop(get_engine, None)

    assert res.status_code == 200
    body = res.json()
    assert body["engine"] == {"name": "fake-real-engine", "is_prototype": False}
    recs = body["recommendations"]
    assert recs[0]["scheme_id"] == "NSFDC-TL"
    assert recs[0]["score"] == 94
    assert recs[0]["reasons"] == ["Income within applicable limit", "Activity is eligible"]
    # enriched from the database, not from the engine
    assert recs[0]["scheme"]["max_loan_amount"] == 4500000
    assert recs[0]["source_type"] == "prototype_mock"
    # unknown scheme ids pass through without enrichment rather than crashing
    assert recs[1]["scheme_id"] == "UNKNOWN-X"
    assert recs[1]["scheme"] is None
