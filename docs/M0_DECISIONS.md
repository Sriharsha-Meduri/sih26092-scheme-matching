# SIH26092 — M0 Decisions (FROZEN)

Status: FROZEN (M0). All M1 work must respect these decisions.

## A. Decisions Made (PS/PRD-supported)

| ID | Decision | Basis |
|---|---|---|
| D1 | Scope: NSFDC 5 schemes only | PRD §4, §8 |
| D2 | Eligibility = deterministic rules-as-data; LLM never decides eligibility | PRD §7.2, §17 |
| D3 | Ranking weights 40/25/20/15 (scheme factors) and 40/25/20/15 (partner factors); config-driven | PRD §7.2, §7.4 |
| D4 | Modular monolith (one backend, one DB, one frontend) | PRD §11 |
| D5 | Stack: Next.js + FastAPI + PostgreSQL | PRD §12 |
| D6 | Golden fixtures = PRD §24 scenarios (entrepreneur, education, ineligible, partner routing) | PRD §24 |
| D7 | Non-goals frozen from PRD §4 (no approval, no disbursement, no MVP auth, no microservices) | PRD §4 |
| D8 | Logical DB tables per PRD §10 | PRD §10 |
| D9 | Informational disclaimer on all recommendations; never fabricate metrics | PRD §7.4, §9 |
| D10 | RAG = P2 supporting only; chatbot is an interface, not the product | PRD §17 |

## B. Decisions with Recommendation (ambiguity documented)

### B1 — Compendium of Schemes conflict
QUESTION: Is the 2024 Compendium a Primary or Secondary source?
OPTIONS: (a) Primary (as Excel register), (b) Secondary/historical (as JSON S009).
RECOMMENDED: Secondary/historical; never base eligibility numbers on it alone.
REASON: JSON already flags it; PRD "database provides authoritative information"; conflict recorded, not silently resolved.

### B2 — Term Loan lower-bound semantics
QUESTION: Is the ₹1.40L boundary inclusive or exclusive?
OPTIONS: (a) >=₹1.40L, (b) >₹1.40L.
RECOMMENDED: exclusive (`> ₹1.40L`), stored with an explicit inclusive=false flag.
REASON: consistent with JSON `project_cost_min_inclusive: 140000.01` and PIB wording; verify at M1 retrieval.

### B3 — Partner data acquisition
QUESTION: Who ingests partner/performance data?
RECOMMENDED: D1 downloads referenced PDFs into data/ (read-only snapshots) and curates normalized derivatives; D2 loads them into PostgreSQL.
REASON: PRD maps "Data/KB" to the knowledge-base owner; D2 owns runtime schema.

### B4 — Master DB.txt (empty file)
QUESTION: dispose / repurpose / keep?
RECOMMENDED: keep untouched and read-only during M0/M1; disposition decision deferred.
REASON: no content and no PRD reference; deletion requires team consent.

### B5 — intillegence/ directory spelling
RECOMMENDED: rename to intelligence/ at M1 start.
REASON: matches track name and avoids divergence of package/dir names. Not done in M0 (read-only).

### B6 — PII handling
RECOMMENDED: session-only, no default persistence, UI privacy notice.
REASON: PRD auth is a non-goal; minimal demo footprint.

### B7 — ELS course-fee data
RECOMMENDED: user-supplied fee input for the min(₹40L, 90% of course fee) cap; no external fee dataset in MVP.
REASON: PRD defines no fee dataset; avoids external data scope.

### B8 — LLM provider
RECOMMENDED: pluggable wrapper (D3) with deterministic fallback; demo must work without LLM.
REASON: reliability at demo time; PRD treats LLM as supporting.

### B9 — API endpoint naming
RECOMMENDED: adopt PRD §14 paths; final naming during implementation.
REASON: contracts frozen at data level only.

### B10 — Multilingual validation
RECOMMENDED: D3 owns EN/HI/TE strings; translations team-validated (PRD §16). D1 emits English reason keys.
REASON: PRD §16.

## C. Assumptions
- As1: NSFDC web pages are authoritative-current as of retrieval 2026-09-08.
- As2: Partner PDFs referenced in the Excel register remain downloadable.
- As3: Partner geocoding from addresses is feasible (or a demo-friendly sample subset is used).
- As4: Demo partner presence can be satisfied by seeding representative partner data.
- As5: PRD's 4-member team division maps onto our 3 members (AI/Integration → D3; Data/KB → D1).

## D. Risks
| ID | Risk | Mitigation |
|---|---|---|
| R1 | Partner/performance PDF URLs may change or be unavailable | Snapshot into data/ at M1 |
| R2 | Fact-level provenance effort larger than expected | Scope to P0 facts first |
| R3 | Activity taxonomy normalization scope creep | Bound to PRD sample + indicative list |
| R4 | ELS moratorium semantics course-length-dependent | Capture condition as data; verify official source |
| R5 | Repo untracked (no commits); KB unprotected | First commit at M1 start |
| R6 | PS rate range (6.5–8%) vs AMY/UNY (15%/13%) confuses users | UI shows real per-scheme rates with source |
| R7 | LLM dependency at demo | Deterministic fallback path |
| R8 | PII (income, SC status) exposure | Session-only + UI notice |

## E. Decisions Required for M1
1. Confirm B1–B10 (defaults recommended above).
2. Confirm authoritative-source policy (current NSFDC pages primary; Compendium secondary).
3. Confirm source-freshness cadence and version-bump owner (D1).
4. Confirm activity-mapping strategy (rule matrix vs per-activity table).
5. Confirm rule representation schema (PRD §10.2 + operator vocabulary).
6. Confirm intelligence package shape (pure-Python library imported by FastAPI).
7. Confirm which partner/performance data is in-mvp vs demo-seeded.
8. Confirm Master DB.txt disposition (B4).

## F. M1 Entry Criteria (frozen)
M1 = KNOWLEDGE BASE IMPLEMENTATION only:
1. Canonical scheme schema
2. Normalize current scheme data
3. Normalize eligibility rules
4. Build activity taxonomy
5. Build activity→scheme relationships
6. Add/validate authoritative sources
7. Add missing scheme information
8. Establish provenance
9. Create validation rules
10. Create golden test data for the intelligence layer

Not in M1: production backend, APIs, frontend, DB schema creation, intelligence engine code, LLM integration.

## G. Repository Facts Recorded
- PRD lives at docs/prd.md (not SIH26092_PRD.md); no PDF present.
- KB/Master DB.txt is empty. Directory is intillegence/ (see B5).
- M0 created only the four M0_*.md documents; no existing file was modified.