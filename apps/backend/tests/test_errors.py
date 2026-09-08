from fastapi.testclient import TestClient

from app.api import partners as partners_api
from app.main import app
from tests.conftest import HYDERABAD


def test_404_has_structured_shape(client):
    body = client.get("/api/schemes/NOPE").json()
    assert set(body["error"].keys()) >= {"code", "message"}
    assert body["error"]["code"] == "not_found"


def test_422_carries_field_details(client):
    body = client.post("/api/recommend", json={"annual_income": "abc"}).json()
    err = body["error"]
    assert err["code"] == "validation_error"
    assert isinstance(err["details"], list) and err["details"]
    assert all({"loc", "msg", "type"} <= set(d.keys()) for d in err["details"])


def test_unexpected_exception_becomes_500_without_a_stack_trace(session_factory, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("database exploded with sensitive detail")

    monkeypatch.setattr(partners_api.partner_service, "find_nearby", boom)

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            res = c.get("/api/partners/nearby", params=HYDERABAD)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 500
    body = res.json()
    assert body["error"]["code"] == "internal_error"
    assert "sensitive detail" not in res.text
    assert "Traceback" not in res.text
