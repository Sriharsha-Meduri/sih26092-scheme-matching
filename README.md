# SIH26092: AI Scheme Matching for Marginalized Entrepreneurs

Smart India Hackathon 2026. A multilingual, AI assisted platform that helps
eligible beneficiaries find the right government concessional credit or
educational loan scheme, understand why it fits, estimate repayment, and reach a
nearby authorised channel partner.

Core principle from the PRD: AI interprets, rules decide, data proves.

## Layout
```
docs/
  SIH26092_PRD.pdf        product requirements, source of truth
  BACKEND_DESIGN.md       backend architecture, schema, integration plan
  API_CONTRACT.md         the shared REST contract for all three developers
apps/
  backend/                FastAPI + PostgreSQL (Developer 2)
docker-compose.yml        PostgreSQL plus the backend for local development
```
The frontend (Developer 3) and the intelligence dataset and engine (Developer 1)
integrate through the contract in `docs/API_CONTRACT.md` and the engine boundary
described in `docs/BACKEND_DESIGN.md`.

## Quick start
```bash
docker compose up --build
```
Then open http://localhost:8000/docs.

Without Docker, see `apps/backend/README.md`.

## Team
- Developer 1: knowledge base and intelligence (scheme master, rules, recommendation engine)
- Developer 2: backend, database, APIs, calculator, partner routing, deployment
- Developer 3: Next.js frontend, UX, AI conversational interface, multilingual UI
