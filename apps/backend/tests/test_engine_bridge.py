"""Developer 1's real intelligence engine, reached through the module adapter.

These tests run the actual engine against the KB shipped in the repo. If the
`intelligence` package is missing (for example in a stripped deployment) the
tests are skipped rather than failed, so the backend suite stays green."""

import pytest

from app.intelligence.engine import ModuleRecommendationEngine, get_engine
from app.main import app

bridge = pytest.importorskip("app.intelligence.bridge")
try:
    bridge._ensure_importable()
except RuntimeError:  # pragma: no cover
    pytest.skip("intelligence package not available", allow_module_level=True)

ELIGIBLE_PROFILE = {
    "is_sc": True,
    "annual_income": 250000,
    "purpose": "business",
    "activity": "tailoring",
    "project_cost": 300000,
    "education_status": None,
    "course": None,
    "caste_certificate": True,
    "entity_type": "Individual",
    "location": {"lat": 17.385, "lng": 78.4867},
}


def test_missing_inputs_are_reported_not_guessed(client):
    """Without a caste certificate and entity type the engine must not claim
    eligibility; it should tell the UI which fields to ask for."""
    app.dependency_overrides[get_engine] = lambda: ModuleRecommendationEngine("app.intelligence.bridge:recommend")
    try:
        incomplete = {k: v for k, v in ELIGIBLE_PROFILE.items() if k not in ("caste_certificate", "entity_type")}
        res = client.post("/api/recommend", json=incomplete)
    finally:
        app.dependency_overrides.pop(get_engine, None)

    assert res.status_code == 200
    body = res.json()
    assert body["overall_status"] == "INSUFFICIENT_INFORMATION"
    assert not any(r["eligible"] for r in body["recommendations"])
    missing = {m["field"] for m in body["missing_information"]}
    assert {"caste_certificate", "entity_type"} <= missing


def test_bridge_returns_contract_shape_from_real_engine():
    out = bridge.recommend(ELIGIBLE_PROFILE, [])
    recs = out["recommendations"]
    assert recs, "engine returned no schemes"
    for r in recs:
        assert set(r.keys()) >= {"scheme_id", "scheme_name", "eligible", "score", "reasons"}
        assert isinstance(r["eligible"], bool)
        assert r["scheme_id"].startswith("NSFDC-")
    assert any(r["eligible"] for r in recs), "expected at least one eligible scheme for a plainly eligible profile"
    eligible = [r for r in recs if r["eligible"]]
    assert all(r["reasons"] for r in eligible)
    # reasons are the engine's stable i18n keys, upper snake case, never free text
    assert all(k == k.upper() for r in eligible for k in r["reasons"])


def test_bridge_flags_ineligible_income():
    out = bridge.recommend({**ELIGIBLE_PROFILE, "annual_income": 99_000_000}, [])
    recs = out["recommendations"]
    assert recs
    assert not any(r["eligible"] for r in recs)


def test_api_recommend_through_real_engine_is_enriched(client):
    app.dependency_overrides[get_engine] = lambda: ModuleRecommendationEngine("app.intelligence.bridge:recommend")
    try:
        res = client.post("/api/recommend", json=ELIGIBLE_PROFILE)
    finally:
        app.dependency_overrides.pop(get_engine, None)

    assert res.status_code == 200
    body = res.json()
    assert body["engine"]["is_prototype"] is False
    assert body["engine"]["name"].startswith("module:")
    top = body["recommendations"][0]
    assert top["eligible"] is True
    # enrichment comes from our database, not from the engine
    assert top["scheme"] is not None
    assert top["scheme"]["max_loan_amount"] is not None
    assert top["source_type"] is not None


def test_engine_metadata_is_deterministic_and_llm_free():
    meta = bridge.engine_metadata()
    assert meta["deterministic"] is True
    assert meta["llm_used"] is False
