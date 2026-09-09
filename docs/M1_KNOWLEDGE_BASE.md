# M1 — Knowledge Base: Build, Resolver, Contracts & Handoff

**Project:** SIH26092 · **Milestone:** M1 KNOWLEDGE BASE · **Status:** COMPLETE
**Owner:** Knowledge team · **Read this first:** `docs/M0_ARCHITECTURE.md`, `docs/M1_1_KB_AUDIT.md`
**Reproducibility:** `python KB/tools/build_kb.py` && `python KB/tools/validate_kb.py` && `python -m pytest KB/tests`

---

## 1. Purpose and scope of the KB

This milestone turns the three raw artifacts (`KB/SIH26092_Scheme_Master_KB.json`,
`KB/SIH26092_Knowledge_Base_Source_Register.xlsx`, `KB/Master DB.txt`) into a **canonical,
machine-usable, provenance-aware Knowledge Base** for the NSFDC scheme-search experience
loading of Developer 2 (Intelligence Engine).

Scope: **data + knowledge only.** No product code — no UI, no API, no PostgreSQL,
no chat, no EMI calculator, no partner routing. The KB is the deterministic input layer
the future engine reads; everything the engine reports must be derivable from `KB/normalized/*`.

Non-negotiable data policy (carried from M0/M1.1 and enforced by the pipeline):
never invent government facts; never silently infer eligibility; never resolve source
conflicts by guessing; represent missing/unknown explicitly; mark every derived value
with its basis; keep raw artifacts byte-unchanged.

## 2. Reader map

| You want… | Read |
|---|---|
| The whole picture | This document |
| Counts and flags that were open | `docs/M1_1_KB_AUDIT.md` |
| Schema of every entity | `KB/schemas/README.md` (+ each `.schema.json`) |
| The actual data | `KB/normalized/*.json` |
| Why a value looks the way it does | `KB/tools/overlays/curation.json` + `provenance.json` |
| How to re-create everything | `KB/tools/build_kb.py` (read-only inputs) |
| Proof it is correct | `KB/tools/validate_kb.py`, `KB/tests/*` |

## 3. Source artifacts and integrity

| Artifact | Role | Bytes | SHA-256 |
|---|---|---|---|
| `KB/SIH26092_Scheme_Master_KB.json` | Primary structured seed (5 schemes, 7 rules, 25 courses, 148 activities, 9 sources) | 13 546 | e6045072da5068c1cd5f0d2add4c71a3ef2b8d4ea4e6c5bbe0f4d9ef60bf20e6 |
| `KB/SIH26092_Knowledge_Base_Source_Register.xlsx` | Provenance register (33 rows, 10 categories) + Current Scheme Snapshot (5 rows) | 10 776 | 3e89c67beba75672b5031b3d565d48e6f0e1fef96ea9a66e8cd8f26b6ff08c3d |
| `KB/Master DB.txt` | Empty placeholder (0 bytes) — preserved, not a data source (DQ-009) | 0 | e3b0c44298fc1c149afbf4c8996fb924… |

Byte-exact snapshots live in `KB/raw/` (manifest in `KB/raw/README.md`). The validator
re-computes these hashes on every run and fails on any drift. Originals remain untouched.

## 4. Canonical schema overview

`KB/schemas/` (15 JSON Schemas, draft-07; shared defs in `kb_defs.schema.json`).
Schema docs and semantics in `KB/schemas/README.md`.

| Entity | File | Records |
|---|---|---|
| Scheme | `schemes.json` | 5 |
| EligibilityRule | `eligibility_rules.json` | 7 |
| FinancialParameter | `financial_parameters.json` | 51 |
| Sector | `sectors.json` | 3 |
| Activity | `activities.json` | 146 unique (148 raw) |
| ActivitySchemeMapping | `activity_scheme_mappings.json` | 146 activity + 3 sector |
| Education / CourseFamily | `education.json` | 25 families + ELS summary |
| DocumentRequirement | `document_requirements.json` | 1 (rule-verified) |
| Source | `sources.json` | 34 |
| Provenance | `provenance.json` | record + field edges |
| Partner | `partners.json` | 0 (stub, NOT_INGESTED) |
| DataQualityIssue | `data_quality_issues.json` | 13 |
| GoldenFixture | `golden_fixtures.json` | 12 |
| Index (envelope) | `index.json` | — |

## 5. Field / null / availability / derived semantics

- `null` = **the source does not provide this and we will not guess** (distinct from `NOT_SPECIFIED`,
  which means the source says something is not covered, and from `UNKNOWN`).
- `availability` enum: `AVAILABLE | PARTIAL | MISSING | NOT_SPECIFIED | UNKNOWN` (see `kb_defs`).
- `derived: true` + entries in `derived_fields` = value was interpreted/parsed/computed.
  Every derived value has a basis string (in `curation.json` or the record) and a field-level
  provenance edge. Derived values are **verification tickets for M2**, not wholesale facts.
- Conditional values `{"type":"conditional","variable":...,"branches":[{"when":{...},"value":...}]}`
  model channel/state-dependent facts (UNY rate, ELS repayment/moratorium, TL moratorium).
- Operator vocabulary: `== != < <= > >= IN NOT_IN EXISTS NO_CEILING` (per M1.4).

## 6. Schemes (normalized)

Five schemes with stable ids `NSFDC-MFS`, `NSFDC-TL`, `NSFDC-AMY`, `NSFDC-UNY`, `NSFDC-ELS`.
Highlights:
- `status` is deliberately `null` — no source states status; `status_assumption` carries the
  derived `ACTIVE_ASSUMED` judgement with its basis (S001 retrieved 2026-09-08).
- TL lower bound modeled **exclusive**: `cost_bounds.min = 140000`, `min_inclusive = false`
  (raw `140000.01` encoding hack, DQ-001).
- MFS/AMY caps are identical (1,40,000 / 1,25,000); they differ by rate (6.5 vs 15) and channel —
  overlap is real, not an error (M1.1 §10).
- Financing percent is 90 for all five (uniform, consistent with PS "up to 90%").
- ELS is the education scheme: `education.is_education_scheme = true` and references the 25 course families.

## 7. Eligibility rules (E001–E007)

| ID | Scope (normalized) | Field | Operator | Value | Effective |
|---|---|---|---|---|---|
| E001 | ALL_CORE_SCHEMES | community | `==` | Scheduled Caste (SC) | — |
| E002 | ALL_CORE_SCHEMES | annual_family_income | `<=` | 500000 (INR/yr) | 2026-01-07 (derived) |
| E003 | ALL_CORE_SCHEMES | caste_certificate | `EXISTS` | valid certificate | — |
| E004 | SCHEME_GROUP(income_generating) | entity_type | `IN` | Individual | — |
| E005 | SCHEME_GROUP(income_generating) | entity_type | `IN` | Partnership Firm (all members SC; each income ≤5L) | — |
| E006 | SCHEME_GROUP(income_generating) | entity_type | `IN` | Co-operative Society (same condition) | — |
| E007 | EXTERNAL_DOMAIN (Skill Development Training) | annual_family_income | `NO_CEILING` | none | — |

- Rules are **scheme-aware via `scope` objects** (M1.4). `ALL_CORE_SCHEMES` maps to the five;
  `SCHEME_GROUP(income_generating)` to MFS/TL/AMY/UNY; **E007 is EXTERNAL_DOMAIN and must not be
  applied to loan eligibility** (DQ-007).
- Raw operators are preserved in `raw_operator`; source text kept in `original_explanation`.

## 8. Financial parameters (51) — flags and boundaries

- 10 parameters per scheme (cost min/max, loan min/max, financing %, NSFDC rate, beneficiary rate,
  repayment years, moratorium months, installment frequency) + ELS `loan_cap_formula`.
- **Conditionals:** UNY beneficiary rate 13% (Co-op) / 15% (SFB) · ELS repayment 12 (not started) / 10 (started) ·
  ELS moratorium `Course period + 1 year` / `up to 6 months` · TL moratorium 6 (default) / 12 (Plantation/Construction).
- **ELS cap formula** = `min(₹40L, 90% × course_fee)` (DQ-005 tension with `max_loan_amount = ₹40L`
  recorded; engine must use user course fee per M0 B7).
- Loan = `min(financing_percent × cost, loan_max)`; **no EMI computation in M1** (Developer 2).

## 9. Activity taxonomy + activity→scheme mapping

- 148 raw activity entries → **146 unique activities** in 3 sectors
  (Agricultural & Allied 20, Small Industries 51, Service & Transport 77).
  Two exact duplicates (`Bicycle Repairing Shops`, `Saw Mills`) merged into single records
  carrying **both** sector_ids; evidence kept; DQ-013.
- `ActivitySchemeMapping`: NSFDC publishes one indicative taxonomy (S004); per-scheme or
  per-activity lists are **not** in the corpus. Therefore **all 146 activity mappings are
  UNVERIFIED** with `inherit_sector=true` (policy + derivation note in the file, DQ-012).
- **Rule for Developer 2:** taxonomy membership is *evidence*, not a verified eligibility fact.
  The Activity Match scoring factor must treat these mappings as UNVERIFIED until per-activity
  confirmation (M2 + Gemini ticket) — never present them as proof of eligibility.

## 10. Education knowledge

- ELS covered-course families: 25 (`CF-001` Engineering … `CF-025` Doctoral Studies/M.Phil/PhD);
  `levels` parsed from parenthesised lists where present (`level_derived = true`).
- `education_eligibility` for ELS: SC (E001), income ≤ ₹5L (E002, effective 2026-01-07),
  caste certificate (E003), course must be on the covered list, regular full-time professional/
  technical course in India or abroad (per purpose). Course-level differentiation beyond the
  list is NOT_SPECIFIED. ELS is not tied to the activity taxonomy.

## 11. Source registry + provenance

- 34 sources: `S001–S009` from the JSON seed merged with the Excel register by URL;
  `S010–S034` are Excel-only rows (partner lists, lending policies, gov context, PIB evidence,
  documents, stories). S006 (NSFDC Forms) has no register row → category `null`.
- **Recorded, unresolved conflict (DQ-008):** S009 Compendium — JSON says `Secondary/historical`,
  Excel (01_Core) says `Primary`. Both representations kept; `authority_level = CONFLICTED`.
  M0 B1 recommendation: treat as Secondary once official confirmation lands.
- `provenance.json`: record-level edges auto-derived from each entity's `sources` (first = PRIMARY,
  rest = CORROBORATING) plus curated field-level edges for every derived/conditional fact
  (TL bound, ELS repayment/moratorium/cap, UNY rate, S009 conflict).
- Rule/activity/scheme source attribution is by the source register's coverage note —
  the raw seed has no per-fact citations (this is stated in the edge `note`).

## 12. Data-quality registry + conflict policy

13 issues `DQ-001…DQ-013` in `data_quality_issues.json` (format hazards, conditional ambiguities,
internal tension, source conflict, missing/not-specified data, exact-duplicate merges). Policy:
- Conflicts are **carried, never resolved by guessing**; both sides are preserved.
- Severity `WARNING`/`ERROR` issues with `resolution_status = HUMAN_DECISION_REQUIRED` are the
  M2 verification backlog (see §18).

## 13. Partner knowledge (status and gap)

Partner master data is **NOT ingested** (M1.9): `partners.json` is a stub with `ingestion_status =
NOT_INGESTED`, an explicit gap description, and the 13 registered source ids (partner PDFs,
utilisation PDF, performance hub, lending policy PDFs). **Nothing about partners is fabricated**
— no names, locations, coordinates, NPA or utilisation figures, no per-partner eligibility.
Partner routing logic is out of M1 scope (Developer 2). Ingestion path exists in the schema
(`partner.schema.json`); a human decision to download the official PDFs into `data/` is required.

## 14. Validation & reproducibility

- `KB/tools/build_kb.py` reads only `KB/raw/*` + `KB/tools/overlays/*` and writes `KB/normalized/*`.
  Deterministic (proven by test), preserves raw hashes.
- `KB/tools/validate_kb.py`: (1) all schemas valid draft-07; (2) every normalized file validates
  against its schema; (3) referential integrity (scheme/source/activity/sector/id refs);
  (4) raw files byte-match registered SHA-256.
- `docs/M1_PROGRESS.md` records status per milestone + raw integrity at each checkpoint.
- Run: `python KB/tools/build_kb.py && python KB/tools/validate_kb.py && python -m pytest KB/tests`

## 15. Golden test fixtures

12 fixtures (`golden_fixtures.json`, curated in `KB/tools/overlays/golden_fixtures.json`):
PRD hero demo (G001), income at/above ceiling (G002/G003), TL lower bound
exclusive (G005), TL loan bound (G004), multi-scheme match (G006), unsupported activity (G007),
non-SC applicant (G008), missing income → must ask (G009), B.Tech education (G010),
non-covered course (G011), conditional-value oracle unit checks (G012).
`KB/tests/` runs 20 tests under pytest (build determinism, validation, fixture verdicts,
conditional resolutions). The fixture oracle is a minimal deterministic KB evaluator that the
real engine must reproduce.

## 16. How the Intelligence Engine should consume the KB

- **Read path:** load `index.json`, then each entity file; validate on load (schemas are present).
- **Never hardcode:** rates, bounds, rule values, course list all come from `KB/normalized/*`.
- **Eligibility:** evaluate per-scheme using rules (operator map, scope) + financial bounds +
  conditional resolution against the user profile; treat E007 and any EXTERNAL_DOMAIN rule as
  context-only.
- **Derived values:** consume them but the UI must be able to cite the `derived` flag + basis
  (transparency), and M2 should verify them (list in §18).
- **Activity & partners:** Activity is UNVERIFIED ranking input only; partner routing must wait
  for partner ingestion. Never present provisional facts as verified (PRD "Data proves").
- **Sources for UI:** every displayed fact should be able to cite `sources.json` id + URL
  (EN/HI/TE listing from PRD references these ids).

## 17. Deliverables & file inventory

```
docs/M1_PROGRESS.md, docs/M1_KNOWLEDGE_BASE.md        (this report)
KB/raw/                                                (byte-exact snapshots + manifest)
KB/schemas/                                            (15 schemas + README)
KB/normalized/                                         (12 entity files + index)
KB/tools/build_kb.py, validate_kb.py, check_schemas.py
KB/tools/overlays/curation.json, golden_fixtures.json  (interpretation layer)
KB/tests/                                              (20 tests)
```
Raw originals (`Master DB.txt`, `*.xlsx`, `*.json` at `KB/`) are untouched (sizes/hashes verified).

## 18. Handoff checklist: open items for humans & M2

1. **Partner ingestion** — human decision to approve official-PDF download → `data/raw/` parse → `partners.json` (schema ready). [Blocked on decision]
2. **DQ-008 Compendium authority** — confirm Secondary/historical (M0 B1). 
3. **DQ-001 TL bound semantics** — official confirmation that ₹1.40L bound is exclusive (already modeled exclusive).
4. **DQ-002/003/004 conditional rates & terms** — verify UNY 13/15 and ELS 12/10 + moratorium wording against S019–S022 policy PDFs.
5. **DQ-006 E002 effective date** — confirm 2026-01-07 reflects a real policy change.
6. **Per-activity verification (DQ-012)** — 146 activity→scheme mappings, UNVERIFIED → verify via scheme documents + Gemini pass.
7. **DQ-011 document checklists** — confirm final per-scheme documents from application forms (S006).
8. **ELS course-duration inputs** — moratorium depends on course period (M0 B7); user input or course-family duration table needed.
9. **Scheme status field** — `ACTIVE_ASSUMED` needs periodic re-check; add CI freshness check on NSFDC pages.
10. **M2 build contract** — engine must reproduce the golden-fixture oracle outputs exactly.

**M1 STATUS: COMPLETE** (all milestone checkpoints validated; 20/20 tests passing; raw artifacts unchanged).
See the M1 FINAL REPORT supplied with the closing note for the acceptance-criteria checklist disposition.