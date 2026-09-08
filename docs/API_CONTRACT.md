# SIH26092 API Contract

This is the shared contract between all three developers. Do not change a
field name or shape here without telling the team first. The backend
implements exactly this; the frontend consumes exactly this.

Base URL is environment driven. In development: `http://localhost:8000`.
Interactive docs: `/docs`. OpenAPI JSON: `/openapi.json`.

All error responses share one shape:

```json
{ "error": { "code": "not_found", "message": "Scheme not found", "details": null } }
```

Codes: `bad_request` (400), `not_found` (404), `validation_error` (422),
`upstream_error` (502, the intelligence engine failed), `internal_error` (500).

Every scheme and partner carries `source_type` so the UI can label the data:
`official`, `prototype_mock`, or `derived`. Prototype data must be shown as
prototype, never as official.

---

## GET /health

Purpose: liveness, plus whether the database and the recommendation engine are reachable.

Response 200:
```json
{
  "status": "ok",
  "app": "SIH26092 Scheme Matching Backend",
  "version": "0.1.0",
  "env": "development",
  "database": "ok",
  "recommendation_engine": { "name": "mock", "is_prototype": true }
}
```
`database` is `"ok"` or `"error"`. `status` is `"degraded"` if the database check fails.

---

## GET /api/schemes

Purpose: list all active schemes with their key terms and provenance.

Query: none.

Response 200: array of scheme summaries.
```json
[
  {
    "scheme_id": "NSFDC-TL",
    "name": "Term Loan",
    "scheme_type": "term_loan",
    "purpose": "business",
    "target_group": "Scheduled Caste beneficiaries",
    "project_cost_min": null,
    "project_cost_max": 5000000,
    "max_loan_amount": 4500000,
    "financing_percentage": 90,
    "nsfdc_interest_rate": 3,
    "beneficiary_interest_rate": 8,
    "repayment_period_months": 120,
    "moratorium_period_months": 6,
    "installment_frequency": "monthly",
    "application_mode": "through channel partner",
    "status": "active",
    "effective_from": null,
    "effective_until": null,
    "source": {
      "source_type": "prototype_mock",
      "title": "Prototype placeholder data",
      "url": null,
      "authority": null,
      "verification_date": null,
      "version": "prototype",
      "notes": "Placeholder values for development. Not official."
    }
  }
]
```
Any numeric field may be `null`, meaning the value is not available from the
current source. Do not substitute a default in the UI.

---

## GET /api/schemes/{scheme_id}

Purpose: full detail for one scheme, including its stored eligibility rules and
application document requirements.

Path: `scheme_id` string, e.g. `NSFDC-TL`.

Response 200: the summary fields above, plus:
```json
{
  "eligibility_rules": [
    {
      "field": "annual_income",
      "operator": "<=",
      "value": "300000",
      "unit": "INR",
      "priority": 1,
      "explanation": "Annual family income must be within the applicable limit"
    }
  ],
  "application_requirements": [
    { "document_name": "Caste certificate", "mandatory": true, "description": "Issued by the competent authority" }
  ]
}
```
Errors: 404 `not_found` when the scheme id does not exist.

---

## POST /api/recommend

Purpose: ranked scheme recommendations for a beneficiary profile. The backend
forwards the profile to the intelligence engine and enriches the answer with
scheme data. The backend does not decide eligibility.

Request:
```json
{
  "is_sc": true,
  "annual_income": 350000,
  "purpose": "business",
  "activity": "tailoring",
  "project_cost": 300000,
  "education_status": null,
  "course": null,
  "location": { "lat": 17.385, "lng": 78.4867 }
}
```
Validation: `is_sc` boolean required. `annual_income` number >= 0 required.
`purpose` one of `business`, `education`. `activity`, `education_status`,
`course` optional strings. `project_cost` optional number >= 0. `location`
optional, `lat` in [-90, 90], `lng` in [-180, 180].

Response 200:
```json
{
  "recommendations": [
    {
      "scheme_id": "NSFDC-TL",
      "scheme_name": "Term Loan",
      "eligible": true,
      "score": 94,
      "reasons": [
        "Income within applicable limit",
        "Activity is eligible",
        "Project cost fits scheme"
      ],
      "scheme": {
        "max_loan_amount": 4500000,
        "financing_percentage": 90,
        "beneficiary_interest_rate": 8,
        "repayment_period_months": 120,
        "moratorium_period_months": 6,
        "project_cost_min": null,
        "project_cost_max": 5000000
      },
      "source_type": "prototype_mock"
    }
  ],
  "engine": { "name": "mock", "is_prototype": true },
  "disclaimer": "Based on the configured eligibility rules and available scheme information, these schemes appear to match your profile. This is guidance, not a government approval."
}
```
Recommendations are sorted eligible first, then by score descending.
Ineligible schemes are included with `eligible: false` so the UI can explain
why. `score` is an internal ranking score from 0 to 100, not a probability.
When `engine.is_prototype` is true the reasons come from the placeholder engine
and must be shown as prototype output.

Errors: 422 `validation_error`; 502 `upstream_error` if the engine cannot be reached.

---

## POST /api/calculate-emi

Purpose: an estimated repayment schedule summary. This is an estimate, not an
official lender schedule.

Request:
```json
{
  "loan_amount": 300000,
  "interest_rate": 8,
  "tenure_months": 60,
  "moratorium_months": 3,
  "scheme_id": "NSFDC-TL"
}
```
Validation: `loan_amount` > 0 required. `interest_rate` >= 0; may be omitted
only when `scheme_id` is given and that scheme has a stored beneficiary rate.
`tenure_months` integer > 0 required. `moratorium_months` integer >= 0, default 0.
`scheme_id` optional; if given it must exist.

Method (stated so nobody guesses): reducing balance EMI. During the moratorium
no instalments are paid and simple interest accrues on the principal; that
interest is added to the principal when instalments start. Instalments then run
for `tenure_months`, so total duration is moratorium plus tenure. Zero interest
divides the principal evenly.

Response 200:
```json
{
  "loan_amount": 300000,
  "interest_rate": 8,
  "tenure_months": 60,
  "moratorium_months": 3,
  "monthly_emi": 6205.37,
  "total_interest": 72322.07,
  "total_repayment": 372322.07,
  "total_duration_months": 63,
  "moratorium_interest": 6000,
  "principal_after_moratorium": 306000,
  "is_estimate": true,
  "method": "Reducing balance EMI. Simple interest accrues during the moratorium and is added to the principal before instalments begin. Estimate only; lender schedules may differ.",
  "scheme": {
    "scheme_id": "NSFDC-TL",
    "scheme_name": "Term Loan",
    "max_loan_amount": 4500000,
    "within_scheme_limit": true,
    "interest_rate_source": "request"
  }
}
```
`scheme` is `null` when no `scheme_id` was sent. `within_scheme_limit` is
`null` when the scheme has no stored limit. `interest_rate_source` is
`"request"` or `"scheme"`.

Errors:
- 400 `bad_request` with message `loan_amount exceeds the scheme limit of X`
  when `loan_amount` is above the scheme's `max_loan_amount`.
- 400 `bad_request` when `interest_rate` is missing and the scheme has no rate.
- 404 `not_found` for an unknown `scheme_id`.
- 422 `validation_error` for invalid numbers.

---

## GET /api/partners/nearby

Purpose: channel partners near a location, filtered for the selected scheme and
ranked by the documented formula.

Query:
- `lat` number, required, [-90, 90]
- `lng` number, required, [-180, 180]
- `scheme_id` string, optional
- `radius_km` number, optional, > 0, default 50, max 500
- `limit` integer, optional, 1 to 100, default 10

Example: `GET /api/partners/nearby?lat=17.3850&lng=78.4867&scheme_id=NSFDC-TL`

Response 200:
```json
{
  "query": { "lat": 17.385, "lng": 78.4867, "scheme_id": "NSFDC-TL", "radius_km": 50, "limit": 10 },
  "count": 3,
  "ranking_method": "Weighted score: scheme compatibility 40, distance 25, verified performance 20, availability 15. Missing data scores zero and is reported as unavailable.",
  "results": [
    {
      "partner_id": "PSB-HYD-001",
      "name": "State Bank branch, Abids",
      "partner_type": "PSB",
      "address": "Abids, Hyderabad",
      "state": "Telangana",
      "district": "Hyderabad",
      "latitude": 17.3907,
      "longitude": 78.4761,
      "distance_km": 1.3,
      "phone": null,
      "email": null,
      "website": null,
      "status": "active",
      "scheme_compatibility": {
        "scheme_id": "NSFDC-TL",
        "authorization_status": "authorized",
        "compatible": true,
        "geographic_scope": "Telangana"
      },
      "performance": {
        "available": false,
        "period": null,
        "sanctioned_amount": null,
        "disbursed_amount": null,
        "utilization_percentage": null,
        "npa_percentage": null,
        "overdue_amount": null,
        "status": null,
        "as_of_date": null
      },
      "rank_score": 79.5,
      "source_type": "prototype_mock"
    }
  ]
}
```
Rules the UI can rely on:
- Partners explicitly `not_authorized` for the scheme are not returned.
- `compatible` is `true` for `authorized`, `null` for `unknown`. Never assume
  `null` means yes.
- `performance.available` is `false` when no verified row exists; every metric
  is then `null`. Show it as unavailable.
- When no `scheme_id` is given, `scheme_compatibility` is `null` and all
  partners in range are returned.

Errors: 422 `validation_error` for bad coordinates or radius; 404 `not_found`
for an unknown `scheme_id`.

---

## GET /api/partners/{partner_id}

Purpose: one partner with all its scheme mappings and its performance record.

Response 200:
```json
{
  "partner_id": "PSB-HYD-001",
  "name": "State Bank branch, Abids",
  "partner_type": "PSB",
  "address": "Abids, Hyderabad",
  "state": "Telangana",
  "district": "Hyderabad",
  "latitude": 17.3907,
  "longitude": 78.4761,
  "phone": null,
  "email": null,
  "website": null,
  "status": "active",
  "schemes": [
    { "scheme_id": "NSFDC-TL", "scheme_name": "Term Loan", "authorization_status": "authorized", "geographic_scope": "Telangana" }
  ],
  "performance": { "available": false, "period": null, "sanctioned_amount": null, "disbursed_amount": null, "utilization_percentage": null, "npa_percentage": null, "overdue_amount": null, "status": null, "as_of_date": null },
  "source": { "source_type": "prototype_mock", "title": "Prototype placeholder data", "url": null, "authority": null, "verification_date": null, "version": "prototype", "notes": "Placeholder values for development. Not official." }
}
```
Errors: 404 `not_found`.

---

## The demo journey, end to end

1. `POST /api/recommend` with the beneficiary profile. Take the top `scheme_id`.
2. `POST /api/calculate-emi` with that `scheme_id` and the chosen loan amount.
3. `GET /api/partners/nearby?lat=..&lng=..&scheme_id=..`.
4. `GET /api/schemes/{scheme_id}` and show `application_requirements` as the next steps.
