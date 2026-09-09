# SIH26092 Backend: Assessment, Architecture and Plan

Project: MoSJE AI Scheme Matching for Marginalized Entrepreneurs (SIH 2026)
Role: Developer 2, Backend and Systems
Source of truth: `docs/SIH26092_PRD.pdf` (PRD v1.0)

This document is the design deliverable that was asked for before implementation:
repository assessment, architecture, database schema, API architecture, service
architecture, integration with the other two developers, phases, and the risks and
assumptions behind it all. The implementation follows this document.

## 1. Repository assessment

When I inspected the repository (`SIH2026/`) it contained a single file, the SIH
shortlist PDF, and nothing else. No git history, no code, no configuration, no
package manager setup, no backend, no database configuration, no Docker, and no
API documentation. The PRD lived on the Desktop, outside the repo.

So this is a greenfield project. There was nothing to preserve or work around.
I initialised git, brought the PRD into `docs/`, and laid down the structure
below. The frontend (Developer 3) and the intelligence dataset (Developer 1) do
not exist in the repo yet; the backend is designed so both can land later
without touching backend architecture.

## 2. Project structure

```
SIH2026/
  docs/
    SIH26092_PRD.pdf           the PRD, source of truth
    BACKEND_DESIGN.md          this document
    API_CONTRACT.md            the shared endpoint contract for all three developers
  apps/
    backend/
      app/
        main.py                app factory, CORS, error handlers, routers
        core/                  settings and structured errors
        db/                    engine, session, seed data
        models/                SQLAlchemy tables
        schemas/               Pydantic request and response models
        repositories/          database queries (no business logic)
        services/              financial calculator, partner routing, recommendation orchestration
        intelligence/          the recommendation engine boundary (protocol, mock, adapters)
        api/                   FastAPI route handlers (thin)
      migrations/              Alembic
      scripts/seed.py          loads clearly labelled prototype data
      tests/                   pytest
      Dockerfile, .env.example, README.md
  docker-compose.yml           Postgres plus backend for local dev
```

This matches the structure the brief asked for. I did not add layers for the
sake of it: repositories exist only for the handful of queries that are reused,
and route handlers hold no logic.

## 3. Backend architecture

Modular monolith, one FastAPI process, one PostgreSQL database, exactly as the
PRD decides in section 11. Request flow:

```
Frontend (Next.js)
   |  REST / JSON
   v
FastAPI route          validates input with Pydantic, nothing else
   v
Service                orchestrates, applies backend-owned logic
   v
Repository / Adapter   database queries, or the intelligence engine boundary
   v
PostgreSQL / Engine
```

Three rules that the code enforces, taken straight from the brief and PRD:

- The frontend never touches the database. It only sees REST.
- The backend never decides eligibility. That belongs to Developer 1's engine,
  reached through an adapter. The backend orchestrates and enriches.
- AI does not decide eligibility. The backend response wording is
  "based on the configured eligibility rules and available scheme information,
  this scheme appears to match your profile", never "AI thinks you are eligible".

Geospatial: I chose plain latitude and longitude with a Haversine service rather
than PostGIS. The PRD allows it, it keeps tests runnable on SQLite without Docker,
and at prototype scale (tens of partners) a Python distance calculation is
instant. PostGIS is a later optimisation with a one-line swap point in the
partner repository.

## 4. Database schema

Designed from PRD section 10. Every government fact carries a `source_id` so
nothing is presented without provenance. Financial and performance fields are
nullable on purpose: a missing value means "unavailable", never a default.

### sources
Provenance registry. `id` PK, `title`, `url`, `source_type`
(`official` | `prototype_mock` | `derived`), `authority`, `published_date`,
`effective_date`, `verification_date`, `retrieved_at`, `version`, `notes`,
`created_at`. Index on `source_type`.

### schemes
`id` PK, `scheme_id` unique (business key, e.g. `NSFDC-TL`), `name`,
`scheme_type`, `purpose` (`business` | `education`), `project_cost_min`,
`project_cost_max`, `max_loan_amount`, `financing_percentage`,
`nsfdc_interest_rate`, `beneficiary_interest_rate`, `repayment_period_months`,
`moratorium_period_months`, `installment_frequency`, `target_group`,
`application_mode`, `status` (`active` | `inactive`), `effective_from`,
`effective_until`, `source_id` FK, `created_at`, `updated_at`.
Indexes on `scheme_id`, `purpose`, `status`. All money and rate columns nullable.

### eligibility_rules
Stored as data, evaluated by Developer 1, exposed read-only by the backend.
`id` PK, `scheme_id` FK, `field`, `operator`, `value`, `unit`, `priority`,
`explanation`, `source_id` FK, `effective_from`, `effective_until`.
Index on `scheme_id`.

### activities
Government activity taxonomy. `id` PK, `name` unique, `sector`, `sub_sector`,
`keywords` JSON, `aliases` JSON.

### els_courses
Educational Loan Scheme course categories. `id` PK, `course_name`, `category`,
`level`, `notes`, `source_id` FK.

### application_requirements
`id` PK, `scheme_id` FK, `document_name`, `mandatory` bool, `description`,
`source_id` FK. Index on `scheme_id`.

### partners
`id` PK, `partner_id` unique, `name`, `partner_type`
(`SCA` | `PSB` | `RRB` | `NBFC_MFI` | `OTHER`), `state`, `district`, `address`,
`latitude`, `longitude`, `phone`, `email`, `website`, `status`
(`active` | `inactive` | `unknown`), `source_id` FK, `created_at`, `updated_at`.
Indexes on `partner_id`, `status`, and `(latitude, longitude)`.

### scheme_partner_mapping
`id` PK, `scheme_id` FK, `partner_id` FK, `authorization_status`
(`authorized` | `not_authorized` | `unknown`), `geographic_scope`, `source_id` FK.
Unique on `(scheme_id, partner_id)`.

### partner_performance
Only ever filled from a verified source. `id` PK, `partner_id` FK, `period`,
`sanctioned_amount`, `disbursed_amount`, `utilization_percentage`,
`beneficiary_count`, `pending_amount`, `npa_percentage`, `overdue_amount`,
`status`, `as_of_date`, `source_id` FK. Every metric nullable. No row means
"unavailable" and the API says so explicitly.

Not built now: `faqs` (P2 in the PRD) and pgvector. Both slot in later without
touching existing tables.

## 5. API architecture

All endpoints are under `/api` except the health check. Full request, response,
validation, and error details for each are in `docs/API_CONTRACT.md`, which is
the shared contract. Summary:

| Method | Path | Purpose |
|---|---|---|
| GET | /health | liveness plus database and engine status |
| GET | /api/schemes | list active schemes with provenance |
| GET | /api/schemes/{scheme_id} | full scheme, its rules and its document requirements |
| POST | /api/recommend | ranked recommendations via the intelligence engine |
| POST | /api/calculate-emi | scheme aware EMI estimate |
| GET | /api/partners/nearby | compatible partners ranked by the documented formula |
| GET | /api/partners/{partner_id} | partner detail with scheme mappings and performance |

Every error is structured JSON: `{ "error": { "code", "message", "details?" } }`.
Stack traces and raw database errors never reach the client. Validation is
backend side with Pydantic and is never delegated to the frontend.

## 6. Service architecture

- `financial_service`: the EMI calculator. Pure function, no database inside,
  so it is trivially testable. The route wraps it with scheme context.
- `partner_service`: Haversine distance, scheme compatibility, and the ranking
  formula. Geospatial maths stays out of route handlers.
- `recommendation_service`: builds the beneficiary profile, hands it to the
  engine through the adapter, then enriches the engine's answer with scheme
  data from the database and attaches the engine identity and the disclaimer.
- `intelligence/engine.py`: the boundary. A `RecommendationEngine` protocol and
  three implementations: `MockRecommendationEngine` (development), an HTTP
  adapter, and an in-process module adapter. Chosen by environment variable.

### The EMI method, stated plainly
Standard reducing balance EMI. During the moratorium no instalments are paid and
simple interest accrues on the principal; that interest is added to the
principal when instalments begin. Instalments then run for `tenure_months`, so
the total duration is moratorium plus tenure. Zero interest divides the
principal evenly. The response is labelled an estimate and names this method,
because lenders differ in how they treat a moratorium.

### The partner ranking formula, stated plainly
Weights follow the PRD (section 7): compatibility 40, distance 25, performance
20, availability 15. Each component scores 0 to 1 and the total is scaled to
0 to 100. Compatibility is 1 only for an `authorized` mapping. Distance is
`1 - (distance / radius)`. Performance uses verified utilisation when a row
exists. Availability is 1 for `active`. Whenever a component's data is missing
it contributes zero and the response marks it unavailable. Missing data is never
treated as a good signal. Partners explicitly `not_authorized` for the chosen
scheme are excluded.

## 7. Integration with Developer 1 (intelligence)

The boundary is a Python protocol with one method:

```
recommend(profile: BeneficiaryProfile, schemes: list[SchemeContext]) -> EngineResult
```

Input is exactly the conceptual profile from the brief (`is_sc`, `annual_income`,
`purpose`, `activity`, `project_cost`, `education_status`, `course`, optional
location). Output is exactly the conceptual result (`recommendations` with
`scheme_id`, `scheme_name`, `eligible`, `score`, `reasons`).

Developer 1 can plug in three ways, selected by `RECOMMENDATION_ENGINE`:

- `mock`: the backend's own placeholder, default in development.
- `module`: an importable Python callable, e.g.
  `RECOMMENDATION_ENGINE_MODULE=intelligence.engine:recommend`. Fastest for a
  monorepo.
- `http`: a service URL, e.g. `RECOMMENDATION_ENGINE_URL=http://engine:8001/recommend`,
  if they prefer to run separately.

Nothing outside `intelligence/` knows which one is active.

Update after Developer 1's engine landed: their engine is a class with its own
request and response dataclasses, so `app/intelligence/bridge.py` translates
both ways and is the `module` target (`app.intelligence.bridge:recommend`). It
adds two optional request fields the engine needs to confirm eligibility,
`caste_certificate` and `entity_type`, and passes the engine's
`overall_status` and `missing_information` through to the API so the UI can
ask for what is missing instead of the backend guessing. The Docker build
context is the repository root so `intelligence/` and `KB/` ship in the image. The mock is clearly
labelled: every response carries `engine.is_prototype: true` and reasons that
begin with "Prototype engine". It uses only fields already stored on the scheme
rows; it contains no government eligibility rules of its own, so it cannot drift
into Developer 1's territory.

Developer 1 also owns the data that fills `schemes`, `eligibility_rules`,
`activities`, `els_courses`, `application_requirements` and `sources`. They load
verified rows into the same tables and the API serves them unchanged. No Python
changes are needed when government information changes.

## 8. Integration with Developer 3 (frontend)

The frontend talks only to REST. It gets:

- Swagger at `/docs` and the OpenAPI JSON at `/openapi.json`, generated from the
  Pydantic models with examples on every endpoint.
- `docs/API_CONTRACT.md` with every request, response, validation rule and error.
- CORS driven by `CORS_ORIGINS`; localhost in development, the deployed
  frontend origin in production.
- A base URL via environment (`NEXT_PUBLIC_API_URL` on their side), never a
  hardcoded localhost.
- Provenance on every scheme and partner (`source_type`) so the UI can label
  official versus prototype data, which the PRD calls out as a UX principle.

The demo journey they will wire is: `POST /api/recommend` then
`POST /api/calculate-emi` with the chosen `scheme_id` then
`GET /api/partners/nearby?scheme_id=...`, then the scheme's
`application_requirements` for the guidance step.

## 9. Development phases

1. Foundation: FastAPI app, settings, structured errors, health endpoint, Docker Compose with Postgres.
2. Database: models, Alembic migration, seed script with labelled prototype data.
3. Scheme APIs.
4. Recommendation API and the engine adapter with the mock.
5. Financial calculator.
6. Partner database and detail API.
7. Geospatial routing with the documented ranking.
8. Tests, including the end to end demo journey.
9. Frontend integration aids: contract, examples, CORS.
10. Deployment: Dockerfile, environment, instructions.

Each phase is a separate commit and is tested before the next begins.

## 10. Risks and assumptions

Assumptions I made where the PRD is silent, each kept as small as possible:

- The seed data is a placeholder. The five NSFDC schemes named in the PRD are
  created with their names and purposes, but their numeric terms are prototype
  placeholders flagged `source_type = prototype_mock` with a note saying so.
  Developer 1 replaces them with verified values. Nothing in the seed is
  presented as official.
- Purpose is limited to `business` and `education`, the two the PRD describes.
- Partner routing excludes partners explicitly not authorised for the selected
  scheme and keeps "unknown" ones visibly flagged rather than hiding them.
- Interest rate in the EMI request may be omitted when a `scheme_id` is given
  and the scheme has a stored beneficiary rate; otherwise it is required.
- Default search radius is 50 km, capped at 500 km.

Risks worth knowing:

- If Developer 1's engine changes the output shape, the adapter is the single
  place to absorb it; the public contract stays fixed.
- Real partner performance data may never arrive for the hackathon. The system
  is built to say "unavailable" honestly, which the PRD treats as a feature.
- PostGIS is deferred. If partner counts grow into the thousands the Haversine
  scan becomes the first thing to replace.
