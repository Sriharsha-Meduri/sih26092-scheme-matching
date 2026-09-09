# SIH26092 — M0 Architecture (FROZEN)

Status: FROZEN (M0). Read-only reference. No production code.

## 1. Final Problem Definition

### 1.1 Target users
- Persona 1: Marginalized SC entrepreneur (e.g., family income ₹3.5L, starting a ₹3L tailoring business)
- Persona 2: SC student seeking education financing (e.g., B.Tech)
- Persona 3: Existing small business owner seeking additional financing
- Secondary: SIH judges (need a working, explainable end-to-end demo)

### 1.2 User problems
1. Cannot identify which NSFDC scheme fits their purpose
2. Cannot assess their own eligibility (SC status, income ≤ ₹5L, entity type)
3. Cannot compute loan amount / EMI / repayment / moratorium
4. Cannot find an authorized channel partner that can process the scheme
5. Cannot understand WHY a scheme/partner is recommended (no explainability)
6. Language barrier (multilingual support required: EN/HI/TE)

### 1.3 Government/system problems (FACT)
- Direct loan applications are not accepted; funds route via the Channel Finance System (100+ partners: SCAs, PSBs, RRBs, NBFC-MFIs)
- Fragmented scheme information across government documents
- Misrouted applications and disbursement delays
- Partner fund-utilization / NPA overdues matter for routing (verified data availability varies)

### 1.4 Desired solution (FACT, PRD §1.2)
A multilingual, mobile-first web platform converting natural-language requirements into: eligible scheme → explainable recommendation → financial estimate → suitable nearby channel partner → application guidance.

### 1.5 Core user journey (MVP)
User provides basic inputs → system interprets → eligibility check → ranked recommendations with reasons → EMI estimate → nearby compatible partners → next steps.

### 1.6 MVP scope (FACT, PRD §8/§21)
- 5 NSFDC schemes: MFS, Term Loan, AMY, UNY, ELS
- P0: scheme database, deterministic eligibility, recommendation engine, EMI calculator, partner database + search + map, frontend, backend APIs
- P1: explainable recommendations, multilingual UI, document checklist
- P2 (out of MVP): RAG, admin dashboard, analytics, advanced performance ranking, user accounts

### 1.7 Explicitly out of scope (FACT, PRD §4)
Loan disbursement; full government backend integration; production-grade auth; underwriting/credit scoring/fraud detection; microservices/K8s; native mobile apps; coverage of all Indian schemes; guaranteed loan approval.

## 2. System Architecture

Conceptual flow (M0 brief):

```
User → Frontend → Backend/API → Intelligence Engine → Knowledge Base
Backend → PostgreSQL | Financial Calculator | Partner Router | Mapping service
```

Final logical architecture (accepted in M0):

```
[User / Browser]
      │ HTTPS
      ▼
[Frontend - Next.js]                     (D3: UX, assessment, results, map, chat)
      │ REST/JSON
      ▼
[Backend API - FastAPI]                  (D2: hosting, orchestration, validation, DB access)
      │                     │                          │                     │
      │ read/write          │ import (lib)             │ calls              │ calls
      ▼                     ▼                          ▼                     ▼
[PostgreSQL]      [Intelligence Engine lib]    [Financial Calculator]  [Partner Router]
(D2 schema/ops)   (D1 pure-Python lib)        (D2)                    (D2)
      ▲                     │                                          │
      │                     ▼                                          ▼
[seed data from   [Knowledge Base masters +                  [Mapping/Geo service
 KB (D1 curates)]  derived + provenance]                      - Leaflet + OSM]
                          (read-only)
                                                                   │
                                                             [LLM integration
                                                              - D3 only, non-eligibility]
                                                                   │
                                                             [Multilingual layer
                                                              - D3 renders i18n keys from D1]
```

### Communication rules
- Frontend communicates ONLY with the Backend API (no direct DB/KB access).
- Backend communicates with: PostgreSQL (read/write), Intelligence (in-process library), Calculator (in-process), Partner Router (in-process), LLM (via wrapper).
- Intelligence Engine communicates ONLY with the Knowledge Base (read-only) and receives structured user profile/requirement.
- No circular dependencies: KB → Intelligence → Backend → DB → Frontend. Financial/route logic lives in Backend.

## 3. Component Ownership (3 developers — no overlap)

| Component | Owner | Boundary |
|---|---|---|
| Knowledge Base masters + derivatives + provenance | D1 | KB/ (read-only) + data/ generated derivatives |
| Intelligence Engine (rules, matching, ranking, explanations, gap detection) | D1 | pure-Python library |
| Golden test fixtures | D1 | shared with all |
| Backend API + FastAPI hosting | D2 | hosts D1 library |
| PostgreSQL schema + seed loading + DB operations | D2 | applies D1 seeds |
| Financial Calculator | D2 | in Backend |
| Partner Router + geo/distance | D2 | in Backend |
| Frontend (Next.js) + multilingual UX + map UI | D3 | consumes D2 API |
| LLM extraction / chat / RAG-lite | D3 | non-eligibility |

## 4. Intelligence Boundary
### Inside (D1)
- Structured input normalization
- Activity classification / alias resolution
- Deterministic eligibility evaluation
- Scheme candidate generation
- Scheme matching / candidate filtering
- Recommendation ranking (40/25/20/15 configurable weights)
- Recommendation explanation (i18n reason keys + source refs)
- Missing-information detection
- Source/provenance reporting

### Outside
- EMI math, geo/distance computation, partner distance ranking → D2
- LLM extraction / chat / RAG → D3
- DB persistence → D2

### Deterministic vs Generative (FACT, PRD §7.2/§17)
- Eligibility = DETERMINISTIC rules + authoritative data. Never LLM-dependent.
- LLM = understanding natural language + supporting explanation only.
- Government eligibility facts must NEVER depend solely on an LLM.

## 5. Knowledge Base Boundary
- RAW SOURCE DATA: NSFDC pages, PDFs, PIB releases, source register (KB/ + data/) — read-only.
- NORMALIZED DATA: typed structures derived from raw (M1 builds these; originals untouched).
- RULES: typed eligibility conditions (E001–E007; PRD §10.2).
- DERIVED DATA: computed values (e.g., financing %, feasibility checks) — explicitly marked as derived.
- PROVENANCE: source_id, source_url, authority, published/effective date, retrieval timestamp, version.

## 6. Database Boundary
### PostgreSQL owns
Application/session data; partner data tables; partner_performance; operational state; geospatial/search data where appropriate; audit/log where appropriate.

### Knowledge Base owns
Government scheme knowledge; eligibility rules; scheme parameters; activity taxonomy + activity→scheme mappings; sources/provenance.

Note: partners and performance originate as KB-curated derivative data but are loaded into PostgreSQL for D2 routing. D1 remains the authoritative owner of the source material; D2 owns the runtime schema.

## 7. Technology Stack (FINAL decision)
- Frontend: Next.js + TypeScript + Tailwind CSS + shadcn/ui; Leaflet + OpenStreetMap
- Backend: FastAPI + Python + Pydantic + SQLAlchemy
- Database: PostgreSQL (local Docker for dev; Supabase for deployment)
- Intelligence: pure-Python deterministic package (no web framework dependency)
- LLM: pluggable provider wrapper (D3); deterministic fallback so demo works without LLM
- Maps: Leaflet + OSM (free, no API key)
- Auth: none for MVP (PRD non-goal)
- Deployment: Vercel (Next) + Render/Railway (FastAPI) + Supabase (Postgres)
- Secrets: environment variables only; never committed to git
- Testing: pytest (rules, scoring, EMI, golden fixtures), API tests, demo E2E
- Version control: GitHub; first commit at M1 start

## 8. Security & Trust (minimum MVP)
- Input validation at API boundary (types, ranges: income ≥ 0, cost > 0, lat/lng bounds)
- Secrets in env vars; .gitignore; no keys committed
- UI disclaimer on every recommendation: "Informational guidance based on published scheme rules. Not an official government decision or loan approval."
- Never fabricate unavailable metrics; show "not available from current authoritative source"
- Every recommendation reason references its rule + source_id (auditability)
- PII (income, SC status): session-only, no default persistence, privacy notice in UI

## 9. Data Quality + Source Policy (for M1)
- Prefer official government sources (nsfdc.nic.in, socialjustice.gov.in, PIB)
- Preserve source URLs, dates, provenance
- Never silently overwrite conflicting values; record both + flag "needs verification"
- Separate verified facts from derived values
- Track freshness (retrieval timestamp; version bump on change)

## 10. MVP Core User Flow + Failure Cases
### Happy path
Start → basic profile (SC, income, entity type) → requirement (activity/course, cost) → system validates inputs → eligibility check → ranked schemes → reasons → EMI → partner routing → results + next steps.

### Failure cases
- No matching scheme → explicit "none found" with reason
- Insufficient information → missing_fields list drives further questions
- Unsupported activity → closest-match suggestion + flag for review
- Income outside eligibility → clear ineligibility reason
- Requested amount outside scheme limits → explain scheme bounds
- Partner unavailable → show unavailable status, never fabricate
- Data requiring verification → surface source conflict flag

## 11. Repository Facts & Discrepancies Noted
- PRD file lives at docs/prd.md (not SIH26092_PRD.md); no PDF present in repo
- KB/Master DB.txt is empty (0 bytes)
- Directory is spelled intillegence/ (recommend renaming to intelligence/ at M1 start)
- Git repo has no commits (recommend first commit at M1 start)