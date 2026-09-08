# SIH26092 Backend

FastAPI backend for the MoSJE AI Scheme Matching platform. This is the
orchestration and data access layer: it validates input, serves scheme and
partner data with provenance, estimates EMIs, ranks nearby channel partners,
and forwards beneficiary profiles to the intelligence engine. It never decides
eligibility itself.

Design: `../../docs/BACKEND_DESIGN.md`. Contract: `../../docs/API_CONTRACT.md`.

## Run it (two ways)

### With Docker (fastest)
From the repository root:

```bash
docker compose up --build
```

That starts PostgreSQL, applies migrations, loads the prototype seed data, and
serves the API on http://localhost:8000. Swagger is at http://localhost:8000/docs.

### Locally
```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env          # then edit DATABASE_URL if needed
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

You need a PostgreSQL reachable at `DATABASE_URL`. The compose file provides one:
`docker compose up postgres`.

## Tests
No database setup needed; the suite runs on in-memory SQLite.

```bash
pytest
```

## Endpoints
| Method | Path |
|---|---|
| GET | /health |
| GET | /api/schemes |
| GET | /api/schemes/{scheme_id} |
| POST | /api/recommend |
| POST | /api/calculate-emi |
| GET | /api/partners/nearby |
| GET | /api/partners/{partner_id} |

## Environment
See `.env.example`. Secrets never go in the repo. The important ones:

- `DATABASE_URL`, PostgreSQL connection string.
- `CORS_ORIGINS`, comma separated. Restrict to the deployed frontend in production.
- `RECOMMENDATION_ENGINE`, `mock` (default), `module`, or `http`, plus the matching
  `RECOMMENDATION_ENGINE_MODULE` or `RECOMMENDATION_ENGINE_URL`.

## Plugging in the real recommendation engine (Developer 1)
Implement the contract in `app/intelligence/engine.py`:

- In process: expose a callable `func(profile: dict, schemes: list[dict]) -> {"recommendations": [...]}`
  and set `RECOMMENDATION_ENGINE=module` and `RECOMMENDATION_ENGINE_MODULE=your.module:func`.
- As a service: accept the profile dict as a POST body and return the same shape;
  set `RECOMMENDATION_ENGINE=http` and `RECOMMENDATION_ENGINE_URL`.

Nothing else in the backend changes. Load verified scheme, rule, activity,
course, requirement and source rows into the existing tables; the API serves
them unchanged.

## Seed data is a placeholder
`scripts/seed.py` loads clearly labelled prototype data (`source_type =
prototype_mock`). The five schemes named in the PRD are present, but their
numeric terms are placeholders, not official figures. Every response carries
the source type so the UI can label it.

## Deployment
The Dockerfile runs migrations and the seed on start, then serves on `$PORT`
(default 8000). It works as is on Render or Railway with a managed PostgreSQL
(Supabase works too). Set the environment variables above, point
`DATABASE_URL` at the managed database, set `ENV=production`, and restrict
`CORS_ORIGINS` to the deployed frontend. Health check path: `/health`.
