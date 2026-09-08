from app.services.geo import haversine_km
from tests.conftest import HYDERABAD

WARANGAL = {"lat": 17.9689, "lng": 79.5941}


def test_haversine_zero_for_same_point():
    assert haversine_km(17.385, 78.4867, 17.385, 78.4867) == 0


def test_haversine_hyderabad_to_warangal_is_plausible():
    d = haversine_km(HYDERABAD["lat"], HYDERABAD["lng"], WARANGAL["lat"], WARANGAL["lng"])
    assert 120 < d < 150


def test_nearby_without_scheme_filters_by_radius_and_excludes_inactive(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD})
    assert res.status_code == 200
    body = res.json()
    ids = [r["partner_id"] for r in body["results"]]
    assert "PSB-WGL-001" not in ids  # outside the 50 km default
    assert "PSB-HYD-004" not in ids  # inactive
    assert body["count"] >= 5
    assert body["query"]["radius_km"] == 50
    scores = [r["rank_score"] for r in body["results"]]
    assert scores == sorted(scores, reverse=True)
    assert all(r["scheme_compatibility"] is None for r in body["results"])


def test_nearby_with_scheme_applies_compatibility_rules(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD, "scheme_id": "NSFDC-TL"})
    assert res.status_code == 200
    results = res.json()["results"]
    by_id = {r["partner_id"]: r for r in results}

    assert "PSB-HYD-003" not in by_id  # explicitly not authorised is excluded

    assert by_id["PSB-HYD-001"]["scheme_compatibility"]["authorization_status"] == "authorized"
    assert by_id["PSB-HYD-001"]["scheme_compatibility"]["compatible"] is True

    # no mapping at all for this scheme: reported as unknown, never as compatible
    assert by_id["NBFC-HYD-001"]["scheme_compatibility"]["authorization_status"] == "unknown"
    assert by_id["NBFC-HYD-001"]["scheme_compatibility"]["compatible"] is None

    # authorised partners must outrank unknown ones
    assert by_id["PSB-HYD-001"]["rank_score"] > by_id["NBFC-HYD-001"]["rank_score"]


def test_missing_performance_is_reported_as_unavailable(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD, "scheme_id": "NSFDC-TL"})
    by_id = {r["partner_id"]: r for r in res.json()["results"]}
    perf = by_id["PSB-HYD-001"]["performance"]
    assert perf["available"] is False
    assert perf["utilization_percentage"] is None
    assert perf["npa_percentage"] is None


def test_verified_performance_is_surfaced_when_present(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD, "scheme_id": "NSFDC-TL"})
    by_id = {r["partner_id"]: r for r in res.json()["results"]}
    perf = by_id["SCA-TS-001"]["performance"]
    assert perf["available"] is True
    assert perf["utilization_percentage"] == 62.5
    assert perf["period"] == "FY2025-26 Q1"


def test_radius_and_limit_are_respected(client):
    wide = client.get("/api/partners/nearby", params={**HYDERABAD, "radius_km": 200}).json()
    assert "PSB-WGL-001" in [r["partner_id"] for r in wide["results"]]

    limited = client.get("/api/partners/nearby", params={**HYDERABAD, "limit": 2}).json()
    assert limited["count"] == 2
    assert len(limited["results"]) == 2


def test_distance_is_reported_and_reasonable(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD}).json()
    for r in res["results"]:
        assert 0 <= r["distance_km"] <= 50


def test_invalid_coordinates_are_422(client):
    assert client.get("/api/partners/nearby", params={"lat": 100, "lng": 78}).status_code == 422
    assert client.get("/api/partners/nearby", params={"lat": 17, "lng": 200}).status_code == 422


def test_radius_above_maximum_is_400(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD, "radius_km": 10000})
    assert res.status_code == 400


def test_unknown_scheme_in_nearby_is_404(client):
    res = client.get("/api/partners/nearby", params={**HYDERABAD, "scheme_id": "NOPE"})
    assert res.status_code == 404


def test_partner_detail(client):
    res = client.get("/api/partners/PSB-HYD-001")
    assert res.status_code == 200
    body = res.json()
    assert body["partner_id"] == "PSB-HYD-001"
    assert body["source"]["source_type"] == "prototype_mock"
    links = {s["scheme_id"]: s for s in body["schemes"]}
    assert links["NSFDC-TL"]["authorization_status"] == "authorized"
    assert body["performance"]["available"] is False


def test_unknown_partner_is_404(client):
    res = client.get("/api/partners/NOPE")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"
