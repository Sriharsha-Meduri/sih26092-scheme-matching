def test_list_schemes_returns_prototype_labelled_rows(client):
    res = client.get("/api/schemes")
    assert res.status_code == 200
    schemes = res.json()
    assert len(schemes) == 5
    ids = {s["scheme_id"] for s in schemes}
    assert {"NSFDC-MFS", "NSFDC-TL", "NSFDC-AMY", "NSFDC-UNY", "NSFDC-ELS"} == ids
    for s in schemes:
        assert s["source"]["source_type"] == "prototype_mock"
        assert s["status"] == "active"


def test_get_scheme_includes_rules_and_requirements(client):
    res = client.get("/api/schemes/NSFDC-TL")
    assert res.status_code == 200
    body = res.json()
    assert body["scheme_id"] == "NSFDC-TL"
    assert body["name"] == "Term Loan"
    assert body["purpose"] == "business"
    assert len(body["eligibility_rules"]) >= 1
    assert any(r["field"] == "annual_income" for r in body["eligibility_rules"])
    assert len(body["application_requirements"]) >= 1
    assert body["source"]["source_type"] == "prototype_mock"


def test_scheme_nullable_fields_are_exposed_as_null(client):
    body = client.get("/api/schemes/NSFDC-ELS").json()
    assert body["project_cost_max"] is None


def test_get_unknown_scheme_returns_structured_404(client):
    res = client.get("/api/schemes/DOES-NOT-EXIST")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"
