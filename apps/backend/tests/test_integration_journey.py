"""The primary demo journey, end to end through the real API:
recommend -> calculate EMI for the top scheme -> nearby partners for that
scheme -> application requirements for the guidance step."""

from tests.conftest import BUSINESS_PROFILE, EDUCATION_PROFILE, HYDERABAD


def test_entrepreneur_journey(client):
    # 1. recommendations
    rec = client.post("/api/recommend", json=BUSINESS_PROFILE)
    assert rec.status_code == 200
    top = rec.json()["recommendations"][0]
    assert top["eligible"] is True
    scheme_id = top["scheme_id"]

    # 2. EMI for the chosen scheme, using the scheme's stored rate
    emi = client.post(
        "/api/calculate-emi",
        json={"loan_amount": 300000, "tenure_months": 60, "moratorium_months": 3, "scheme_id": scheme_id},
    )
    assert emi.status_code == 200
    emi_body = emi.json()
    assert emi_body["scheme"]["scheme_id"] == scheme_id
    assert emi_body["scheme"]["within_scheme_limit"] is True
    assert emi_body["monthly_emi"] > 0
    assert emi_body["is_estimate"] is True

    # 3. nearby compatible partners for that scheme
    partners = client.get("/api/partners/nearby", params={**HYDERABAD, "scheme_id": scheme_id})
    assert partners.status_code == 200
    pbody = partners.json()
    assert pbody["count"] >= 1
    assert pbody["results"][0]["scheme_compatibility"]["scheme_id"] == scheme_id
    assert pbody["results"][0]["scheme_compatibility"]["compatible"] is True

    # 4. application guidance
    detail = client.get(f"/api/schemes/{scheme_id}")
    assert detail.status_code == 200
    assert len(detail.json()["application_requirements"]) >= 1


def test_student_journey(client):
    rec = client.post("/api/recommend", json=EDUCATION_PROFILE)
    assert rec.status_code == 200
    top = rec.json()["recommendations"][0]
    assert top["scheme_id"] == "NSFDC-ELS"
    assert top["eligible"] is True

    emi = client.post("/api/calculate-emi", json={"loan_amount": 800000, "tenure_months": 120, "scheme_id": "NSFDC-ELS"})
    assert emi.status_code == 200
    assert emi.json()["scheme"]["interest_rate_source"] == "scheme"

    partners = client.get("/api/partners/nearby", params={**HYDERABAD, "scheme_id": "NSFDC-ELS"})
    assert partners.status_code == 200
    ids = [r["partner_id"] for r in partners.json()["results"]]
    assert "PSB-HYD-001" in ids


def test_ineligible_applicant_is_explained_not_hidden(client):
    profile = {**BUSINESS_PROFILE, "project_cost": 9000000}  # above every stored business limit
    rec = client.post("/api/recommend", json=profile)
    assert rec.status_code == 200
    recs = rec.json()["recommendations"]
    business = [r for r in recs if r["scheme_id"] != "NSFDC-ELS"]
    assert business and all(r["eligible"] is False for r in business)
    assert all(any("exceeds" in reason for reason in r["reasons"]) for r in business)
