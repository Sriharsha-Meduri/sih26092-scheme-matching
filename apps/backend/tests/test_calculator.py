import pytest

from app.core.errors import BadRequestError
from app.services.financial_service import calculate_emi


def test_standard_emi_matches_known_value(client):
    res = client.post("/api/calculate-emi", json={"loan_amount": 300000, "interest_rate": 8, "tenure_months": 60})
    assert res.status_code == 200
    body = res.json()
    assert abs(body["monthly_emi"] - 6082.92) < 1.0
    assert body["total_duration_months"] == 60
    assert body["moratorium_interest"] == 0
    assert body["is_estimate"] is True
    assert "Estimate only" in body["method"]
    assert body["scheme"] is None
    assert abs(body["total_repayment"] - body["monthly_emi"] * 60) < 1.0


def test_zero_interest_divides_principal_evenly(client):
    res = client.post("/api/calculate-emi", json={"loan_amount": 120000, "interest_rate": 0, "tenure_months": 12})
    assert res.status_code == 200
    body = res.json()
    assert body["monthly_emi"] == 10000
    assert body["total_interest"] == 0
    assert body["total_repayment"] == 120000


def test_moratorium_capitalises_simple_interest(client):
    res = client.post(
        "/api/calculate-emi",
        json={"loan_amount": 300000, "interest_rate": 8, "tenure_months": 60, "moratorium_months": 3},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["moratorium_interest"] == 6000  # 300000 * (8/12/100) * 3
    assert body["principal_after_moratorium"] == 306000
    assert body["total_duration_months"] == 63
    assert abs(body["monthly_emi"] - 6082.92 * 1.02) < 2.0


@pytest.mark.parametrize(
    "payload",
    [
        {"loan_amount": 0, "interest_rate": 8, "tenure_months": 60},
        {"loan_amount": -5, "interest_rate": 8, "tenure_months": 60},
        {"loan_amount": 100000, "interest_rate": -1, "tenure_months": 60},
        {"loan_amount": 100000, "interest_rate": 8, "tenure_months": 0},
        {"loan_amount": 100000, "interest_rate": 8, "tenure_months": 12, "moratorium_months": -1},
        {"interest_rate": 8, "tenure_months": 60},
    ],
)
def test_invalid_inputs_are_422(client, payload):
    res = client.post("/api/calculate-emi", json=payload)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_loan_above_scheme_limit_is_clearly_rejected(client):
    res = client.post(
        "/api/calculate-emi",
        json={"loan_amount": 200000, "interest_rate": 5, "tenure_months": 36, "scheme_id": "NSFDC-MFS"},
    )
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == "bad_request"
    assert "exceeds the scheme limit" in err["message"]
    assert err["details"]["max_loan_amount"] == 140000


def test_scheme_rate_is_used_when_interest_omitted(client):
    res = client.post("/api/calculate-emi", json={"loan_amount": 300000, "tenure_months": 60, "scheme_id": "NSFDC-TL"})
    assert res.status_code == 200
    body = res.json()
    assert body["interest_rate"] == 8
    assert body["scheme"]["scheme_id"] == "NSFDC-TL"
    assert body["scheme"]["interest_rate_source"] == "scheme"
    assert body["scheme"]["within_scheme_limit"] is True


def test_missing_rate_without_scheme_is_400(client):
    res = client.post("/api/calculate-emi", json={"loan_amount": 300000, "tenure_months": 60})
    assert res.status_code == 400


def test_unknown_scheme_is_404(client):
    res = client.post(
        "/api/calculate-emi",
        json={"loan_amount": 1000, "interest_rate": 5, "tenure_months": 12, "scheme_id": "NOPE"},
    )
    assert res.status_code == 404


def test_pure_calculator_validates_its_own_inputs():
    with pytest.raises(BadRequestError):
        calculate_emi(0, 8, 60)
    with pytest.raises(BadRequestError):
        calculate_emi(1000, -1, 60)
    with pytest.raises(BadRequestError):
        calculate_emi(1000, 8, 0)
    with pytest.raises(BadRequestError):
        calculate_emi(1000, 8, 12, -1)
    result = calculate_emi(1000, 0, 4)
    assert result.monthly_emi == 250
