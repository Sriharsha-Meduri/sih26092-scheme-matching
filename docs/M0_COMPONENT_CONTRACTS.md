# SIH26092 — M0 Component Contracts (FROZEN)

Endpoint naming is finalized during implementation (PRD §14 as reference).
Data shapes are frozen now for parallel development.

## 1. Frontend → Backend (REST / JSON)

### POST /api/recommend
INPUT:
```json
{
  "is_sc": true,
  "annual_income": 350000,
  "purpose": "business",
  "activity": "tailoring",
  "project_cost": 300000,
  "education_status": null,
  "course": null,
  "entity_type": "Individual",
  "location": { "lat": 16.5, "lng": 80.6 }
}
```
OUTPUT:
```json
{
  "recommendations": [
    {
      "scheme_id": "NSFDC-TL",
      "scheme_name": "Term Loan",
      "score": 94,
      "reasons": ["income.within_limit", "project_cost.fits_scheme", "activity.eligible"],
      "eligibility": { "eligible": true, "failed_rules": [] },
      "financing": { "max_loan_amount": 4500000, "financing_percentage": 90, "beneficiary_interest_rate": 8 },
      "sources": ["S001"]
    }
  ],
  "missing_fields": [],
  "unavailable_metrics": [],
  "disclaimer": "Informational guidance based on published scheme rules. Not an official government decision or loan approval."
}
```
RESPONSIBILITY: Backend orchestrates D1 intelligence; returns structured payload.
ERROR/FAILURE: 422 validation; 200 with empty `recommendations` + explicit reason when none found.

### GET /api/schemes, GET /api/schemes/{scheme_id}
INPUT: none / scheme_id
OUTPUT: scheme list / detail with financial + source information
RESPONSIBILITY: read scheme master from DB (seeded from KB).
ERROR: 404 unknown scheme.

### POST /api/calculate-emi
INPUT:
```json
{ "scheme_id": "NSFDC-TL", "loan_amount": 300000, "rate": null, "tenure": null, "moratorium": null }
```
OUTPUT:
```json
{ "emi": 0, "total_interest": 0, "total_repayment": 0, "repayment_months": 84, "schedule": [] }
```
Rate/tenure/moratorium default from scheme data unless overridden by user.
RESPONSIBILITY: arithmetic only; parameters come from KB (never hardcoded in UI).
ERROR: 422 validation (non-positive principal / invalid rate).

### GET /api/partners/nearby
INPUT:
```json
{ "scheme_id": "NSFDC-TL", "lat": 16.5, "lng": 80.6, "radius_km": 100 }
```
OUTPUT:
```json
{
  "partners": [
    { "partner_id": "P-001", "name": "...", "partner_type": "SCA", "distance_km": 12.4,
      "scheme_compatible": true, "performance": null, "availability": null, "rank": 1 }
  ]
}
```
`performance`/`availability` = null when the metric is unavailable (never fabricated).
RESPONSIBILITY: geo filter + ranking (scheme compatibility 40%, distance 25%, performance 20%, availability 15%).
ERROR: 422 validation; 200 empty + reason when no authorized partner in radius.

### POST /api/chat  (D3 LLM layer — non-eligibility)
INPUT: natural-language message.
OUTPUT: `{ structured_profile?, reply_text, missing_fields?, disclaimer }`.
RESPONSIBILITY: intent/extraction and guidance only.
ERROR: LLM failure → reply must never block the deterministic flow.

## 2. Backend → Intelligence (in-process library call)

INPUT:
```json
{
  "profile": { "is_sc": true, "annual_income": 350000, "entity_type": "Individual", "education_status": null },
  "requirement": { "purpose": "business", "activity": "tailoring", "project_cost": 300000, "course": null },
  "location": { "lat": 16.5, "lng": 80.6 }
}
```
OUTPUT:
- per-candidate eligibility verdict (pass/fail + rule evidences)
- ranked candidates with factor breakdown (eligibility / activity / financial / partner-availability)
- reasons (i18n keys + parameters)
- missing_fields
- sources (per fact)

RESPONSIBILITY: deterministic eligibility, matching, ranking, explanation, gap detection.
ERROR/FAILURE:
- ambiguous activity → classification with confidence → resolution via alias; else flag
- no candidate → explicit `none_found` + reason
- missing fields → returned in `missing_fields` (do not guess)

## 3. Backend → Financial Calculator (in-process)

INPUT: `{ scheme financial params (from KB), user amount, optional overrides }`
OUTPUT: `{ emi, total_interest, total_repayment, repayment_months, schedule }`
RESPONSIBILITY: arithmetic only.
ERROR: validation for non-positive principal or out-of-range rate.

## 4. Backend → Partner Router (in-process)

INPUT: `{ scheme_id, user location, optional radius/filters }`
READS: partners + scheme_partner_mapping + partner_performance (PostgreSQL, seeded from KB).
OUTPUT: ranked partners with ranked factors; flags for unavailable metrics.
RESPONSIBILITY: geo + partner ranking; never fabricate missing metrics.
ERROR: no authorized partners → explicit empty result + reason.

## 5. Intelligence → Knowledge Base (read-only)

QUERIES: entity retrieval by id; rule lookup by scheme scope; activity by alias; source lookup by source_id.
OUTPUT: entity objects + provenance.
RESPONSIBILITY: read-only access; no writes; no circular dependency.
ERROR: unknown id / missing source → surfaced as `unavailable`, not invented.

## 6. Responsibility Map Recap
- D1: KB masters + derivatives + Intelligence library + fixtures + i18n keys + provenance
- D2: Backend hosting, PostgreSQL schema/seed-load, calculator, partner router, deployment
- D3: Next.js pages, assessment UX, results/calculator/map UI, multilingual UI, LLM wrapper