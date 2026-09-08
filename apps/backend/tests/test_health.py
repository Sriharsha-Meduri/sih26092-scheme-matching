def test_health_reports_ok_with_database_and_engine(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["recommendation_engine"]["name"] == "mock"
    assert body["recommendation_engine"]["is_prototype"] is True
    assert "version" in body and "app" in body
