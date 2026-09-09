# SIH26092 — M2 Intelligence Engine — Design Record

**Project:** SIH26092 · **Milestone:** M2 INTELLIGENCE ENGINE (Deterministic Decision Layer)
**Owner:** Knowledge/D1 team · **Status:** COMPLETE (139 tests green)
**Read first:** `docs/M0_ARCHITECTURE.md`, `docs/M0_DECISIONS.md`, `docs/M0_COMPONENT_CONTRACTS.md`, `docs/M1_KNOWLEDGE_BASE.md`
**Implementation:** `intelligence/` package · **KB consumed read-only:** `KB/normalized/*`

---

## 1. Overview & Milestone Scope

M2 delivers the **Intelligence Engine**: the deterministic, explainable,
provenance-preserving component between the user (web/mobile later) and the M1
canonical Knowledge Base. It answers *"which NSFDC credit/education scheme fits
this applicant, why, and what is still missing"* — without an LLM and without
inventing any fact.

It is a **pure-Python package (`intelligence/`) with zero extra runtime
dependencies** (stdlib only; tests use pytest). It consumes the frozen M1
normalized KB and never writes to it.

Pipeline (all deterministic):
`validate + normalize` → `candidate discovery` → per-candidate
`eligibility · activity · financial · education · partner` → `scoring 40/25/20/15`
→ `ranking + tie-break` → `explanations + sources + gaps` → `response`.

## 2. Constraints & Guardrails

- **No KB/code duplication of government facts.** Every rule/operator/value is
  read from the KB at runtime (`KB/normalized/eligibility_rules.json`,
  `financial_parameters.json`, `schemes.json`, `activities.json`,
  `activity_scheme_mappings.json`, `education.json`, `sources.json`). The Python
  side only knows *how to evaluate*, never *what the values are*.
- **UNKNOWN ≠ FAIL.** A missing input makes its dependent checks UNKNOWN, never
  a rejection; UNKNOWN feeds the gap detector instead (G009).
- **No fabrication.** Partner data is UNAVAILABLE (M1 `partners.json` is a
  `NOT_INGESTED` stub); nothing is invented. `UNVERIFIED` mapping status is
  surfaced, never silently promoted (DQ-012).
- **No LLM** in the decision, scoring, ranking, or explanation path.
- **No FastAPI / frontend / chatbot** in M2 (backend/frontend are later
  milestones). The engine exposes typed-Python + JSON-safe results only.
- **Determinism.** Same KB + same input → same decisions, scores, order,
  reasons, sources. No randomness, no wall-clock dependence.
- **No writes to `KB/`** (repository is read-only).

## 3. System Architecture & Components

```
intelligence/
├── models/            input + output dataclasses (profile, requirement, result, enums)
├── kb/                loader (find KB dir), adapters (pure ops), repository (typed access)
├── normalization/     finance (INR), profile, activity, education, requirement
├── eligibility/       operators (data-driven), rule grouping/combining, evaluator
├── matching/          activity, financial, education, partner dimensions
├── ranking/           scorer (factor breakdown) + ranking (tie-break)
├── explanations/      reason_key constants + structured generator/data
├── gaps/              missing-field detection + aggregation
├── engine.py          RecommendationEngine (public entry)
├── utils.py           JSON-safe dataclass serialization
└── tests/             operators/normalization/eligibility/matching/ranking/engine/golden
```

Entry point (`intelligence/__init__.py`):

```python
from intelligence import RecommendationEngine, ApplicantProfile, Requirement
engine = RecommendationEngine()          # auto-discovers KB/normalized (or SIH26092_KB_DIR)
resp = engine.evaluate(profile, requirement)
# resp.recommendations[].reasons / .warnings / .sources / .eligibility.rule_results ...
```

## 4. Input Contract & Normalization

Typed inputs (`intelligence.models`):
- `ApplicantProfile`: community, is_sc, annual_family_income, caste_certificate,
  entity_type, education_status, employment_status, age, gender.
- `Requirement`: purpose, requirement_type, activity, project_cost,
  requested_loan_amount, course, course_family, education_fee,
  course_duration_years, institution_type, channel_type, activity_category,
  repayment_has_started, location.
- `RecommendationRequest = {profile, requirement, location}`.

Normalization (`intelligence/normalization/`):
- `finance.parse_inr` — "₹3.5L", "5 lakh", "5,00,000", "40 lacs", "1 cr",
  numbers; rejects booleans, NaN/Inf, negative, > 1e12.
- `profile` — community aliases (SC → "Scheduled Caste (SC)", General/non-SC,
  is_sc boolean); entity-type aliases (individual, sole proprietor, partnership
  firm, co-operative/coop → canonical 3).
- `activity` — raw text → canonical M1 activity record (case/whitespace-insensitive,
  alias-aware); unresolved text is preserved raw as UNKNOWN (never invented).
- `education` — course/course_family → one of the 25 covered families
  (`coverage_status LISTED_IN_COVERED_COURSES`). A provided course_family that
  is not listed ⇒ NO_MATCH (G011); an unresolvable raw course ⇒ UNKNOWN.
- `requirement` — purpose inference (activity → business; course only →
  education; neither → unknown), money → INR, conditional flags kept as-is.

Validation is hard-fail (bad types raise) — distinct from "missing" (stays
None, becomes UNKNOWN downstream).

## 5. Candidate Discovery

Deterministic by purpose (`intelligence/engine.py`, M2 §3):

| Purpose | Candidates |
|---|---|
| business | NSFDC-MFS, NSFDC-TL, NSFDC-AMY, NSFDC-UNY |
| education | NSFDC-ELS |
| unknown | none → INSUFFICIENT_INFORMATION |

Early gate (G007): business purpose **and** an activity string that does not
resolve in the M1 taxonomy ⇒ `overall_status = UNSUPPORTED_ACTIVITY`, no
recommendations (the engine cannot claim any scheme finances an unsupported
activity). This is a request-level gate, not a scheme-level one.

## 6. Eligibility Engine

`intelligence/eligibility/` — fully data-driven:
- `operators.apply_operator` implements the M1 schema enum
  (`== != < <= > >= IN NOT_IN EXISTS NO_CEILING`). Each returns True (PASS),
  False (FAIL), or None (UNKNOWN for a missing `actual`). No operator raises on
  supported values; `NO_CEILING` declares "no constraint" and is only reachable
  via an explicit scope override (E007 is EXTERNAL_DOMAIN and is never applied).
- `repository.rules_for_scheme` resolves rule scope:
  `ALL_CORE_SCHEMES`, `SCHEME_GROUP` (income_generating), `SCHEME_LIST`,
  `EXTERNAL_DOMAIN` (excluded from loan eligibility).
- `rules.group_rules` partitions by `condition_group`: grouped rules are
  **OR**-combined (E004/E005/E006 ENTITY_TYPE_ALLOWED); each ungrouped rule is
  its own AND-group (E001/E002/E003 are ANDed, never ORed).
- `evaluator.evaluate_scheme` → `EligibilityResult` with one `RuleResult` per
  evaluated rule (rule_id, name, field, operator, expected, actual, verdict,
  reason_key, scope, sources, DQ issues) plus PASS/FAIL/UNKNOWN rule-id lists
  and verification status.

Known KB truth reproduced by tests: E001 community == SC, E002 income ≤ 5L
(inclusive at exactly 5,00,000), E003 certificate EXISTS (False ⇒ FAIL, missing
⇒ UNKNOWN), income 5,00,001 ⇒ FAIL for all schemes.

## 7. Activity Matching

`intelligence/matching/activity.py` against the M1 activity taxonomy + mapping
(DQ-012: all 146 mappings are UNVERIFIED).

| State | Meaning |
|---|---|
| MATCH | activity resolves and maps to this scheme; `verification = UNVERIFIED` is preserved |
| NO_MATCH | activity resolves but is not mapped to this scheme |
| UNKNOWN | missing (reason `MISSING_ACTIVITY`) or not in taxonomy (`ACTIVITY_UNSUPPORTED`) |
| NOT_APPLICABLE | education case (activity not used for ELS) |

UNVERIFIED is surfaced as a warning and drops the activity factor to 80 (see §10)
— never promoted to a verified fact.

## 8. Financial Fit

`intelligence/matching/financial.py` reads cost bounds, loan bounds, financing %
and financial parameters from the KB (never hardcoded):
- **Inclusivity honours the KB flags:** `min_inclusive=false` means strict
  `>` (TL lower bound 1.40L exclusive — verified by tests: cost 1,40,000 ⇒ TL
  FAIL, 1,40,001 ⇒ PASS); null means inclusive (`<=`). MFS/AMY max 1.40L
  inclusive; UNY max 5L inclusive.
- Eligible amount = `financing_percent × project cost`, capped at `loan_bounds.max`
  (90% for all core schemes).
- **Requested-loan check:** if `requested_loan_amount` provided, must be ≤ the
  eligible amount (else FAIL).
- **ELS cap formula** computed from the KB formula `FP-NSFDC-ELS-011`:
  `min(4,000,000, 90% × course_fee)` — verified (fee 30L ⇒ cap 27L; fee 50L ⇒
  cap 40L).
- **Conditional values** (`resolve_conditionals`): beneficiary rate,
  repayment years, moratorium. Resolved only with user context; otherwise
  reported UNKNOWN `CONDITIONAL_VALUE_UNKNOWN` — never guessed. UNY rate 13
  (Co-operative) / 15 (SFB); ELS repayment 12 when repayment not started, etc.

## 9. Education Matching

`intelligence/matching/education.py` for ELS (others → NOT_APPLICABLE):
- covered course family → MATCH (VERIFIED, coverage `LISTED_IN_COVERED_COURSES`);
- course_family not in the 25 → NO_MATCH (`COURSE_NOT_COVERED`);
- missing course → UNKNOWN (`MISSING_COURSE`); unresolvable raw course →
  UNKNOWN (`COURSE_COVERAGE_UNKNOWN`).

## 10. Scoring & Ranking

Weights frozen (M0 D3): **eligibility 0.40, activity 0.25, financial 0.20,
partner 0.15**. `intelligence/ranking/scorer.py`:

| Factor | State → score |
|---|---|
| eligibility | PASS→100, FAIL→0, UNKNOWN→50 |
| activity | MATCH verified→100, MATCH unverified→80, NO_MATCH→0, UNKNOWN→50, NOT_APPLICABLE→100 |
| financial | PASS→100, FAIL→0, UNKNOWN→50 |
| partner | UNAVAILABLE→0 (weight retained; max achievable total = 85) |

- A factor that does not apply scores 100 with its weight retained (reported
  NOT_APPLICABLE so the UI can show a truthful breakdown).
- Total = Σ(score × weight), 0–100. **This is a matching score, explicitly not
  a probability** and never presented as such.
- Education is folded into the ELS eligibility/composite; not a weighted factor.

Ranking tie-break (`ranking/ranking.py`), deterministic:
1. score descending
2. eligibility factor score
3. financial factor score
4. activity factor score
5. KB scheme-file order (SCHEME_PRIORITY = MFS, TL, AMY, UNY, ELS).

Exact ties keep the **same rank** (ties are intentional, not broken randomly).
The golden fixture orders fall out of this ranking (G001 → [TL, UNY];
G002/G005/G006 → [MFS, AMY, UNY]).

## 11. Partner Availability

`intelligence/matching/partner.py` — M1 partner master is NOT_INGESTED
(`partners.json` stub). Every scheme's partner dimension is **UNAVAILABLE**:
score 0, `reason_key = PARTNER_DATA_UNAVAILABLE`, referencing the registered
PDF source ids (S007/S010–S013…) so the UI can explain the gap. No partner
figure/ranking is fabricated. A future real-partner adapter changes only this
module.

## 12. Gap / Missing-Information Detection

`intelligence/gaps/detector.py` derives gaps **from the structured decision
objects**, never from heuristics:
- eligibility UNKNOWN rules → canonical input fields (community /
  annual_family_income / caste_certificate / entity_type);
- activity UNKNOWN (MISSING_ACTIVITY) → activity;
- financial UNKNOWN (MISSING_PROJECT_COST / MISSING_COURSE_FEE) → project_cost
  / education_fee;
- education UNKNOWN (MISSING_COURSE) → course;
- per scheme the engine lists `missing_fields`; the response aggregates into
  `missing_information` (field → scheme_ids + reason keys).
Provided-but-unresolvable inputs (e.g. activity "Cinema Hall") are **not** gaps
— they are `UNSUPPORTED_ACTIVITY`, a different state.

## 13. Explanation Engine & Provenance

`intelligence/explanations/` — stable **reason keys** (i18n-ready strings, not
free text) + **source refs** with title/url/role, all built from decision facts:
- `collect_reasons` → `reasons` (e.g. COMMUNITY_MATCH, INCOME_WITHIN_LIMIT,
  ACTIVITY_MATCH, ELS_CAP_APPLIED, COURSE_COVERED) and `warnings` (e.g.
  ACTIVITY_UNVERIFIED, CONDITIONAL_VALUE_UNKNOWN, PARTNER_DATA_UNAVAILABLE).
- `collect_sources` → deduplicated `SourceRef`s from rule sources, mapping
  evidence, financial-parameter sources, education family sources and partner
  source ids.
- Every `RuleResult`, factor score, reason and source is traceable to the KB
  record it came from.

## 14. Result Model

`intelligence/models/result.py`:
- `RecommendationResponse` — overall_status (MATCHED / NO_MATCH /
  INSUFFICIENT_INFORMATION / UNSUPPORTED_ACTIVITY), ranked
  `recommendations[]`, `excluded_schemes[]`, `missing_information[]`,
  `request_summary`, `engine_metadata`, disclaimer.
- `SchemeRecommendation` — rank, score, factor_scores, eligibility /
  activity_match / financial_fit / education_fit / partner_fit, reasons,
  warnings, missing_fields, sources, verification_status.
- JSON-serializable via `intelligence.utils.dataclass_to_dict` (enums → values).

## 15. Verification & Unknown-Status Semantics

- Rule-level UNKNOWN ⇒ scheme eligibility `UNKNOWN` ⇒ `verification = UNVERIFIED`
  (never FAIL).
- Composite (helper used by the overall status + golden oracle): PASS = eligibility
  PASS **and** financial PASS **and** (education MATCH for ELS); any FAIL ⇒ FAIL;
  else UNKNOWN.
- Tri-state (M1 contract): any PASS ⇒ eligible True; else any UNKNOWN ⇒ eligible
  None; else eligible False (G001/G003/G008/G009).
- `UNVERIFIED` is surfaced per recommendation and on activity mappings (DQ-012).

## 16. Determinism

- All rules, values and scopes are read in KB order; iteration is stable.
- Ranking uses a fixed key (never `random`, never current time).
- Two runs over the same request produce byte-identical responses (tested).
- `EngineMetadata.deterministic = True`, `llm_used = False`.

## 17. Test Strategy & Golden Fixtures

`intelligence/tests/` — **139 passing, 1 intentionally skipped** (G012 in the
golden loop; its conditional unit checks live in `test_matching.py`):
- `test_operators.py` — full operator truth table + UNKNOWN semantics.
- `test_normalization.py` — INR parsing, community/entity aliases, activity &
  course resolution, purpose inference, validation raises.
- `test_eligibility.py` — E001–E006 grouping (OR/AND), income boundaries
  (5,00,000 inclusive / 5,00,001 fail), UNKNOWN vs FAIL, scope handling
  (EXTERNAL_DOMAIN never applied), ELS all-core rules.
- `test_matching.py` — TL exclusive lower bound, MFS/AMY/UNY caps, requested
  loan, ELS cap formula, conditionals (UNY rate 13/15, TL moratorium, ELS
  repayment), education covered/not/missing, partner unavailable.
- `test_ranking.py` — weights, factor scores (N/A 100, unverified 80, UNKNOWN
  50, partner 0, max 85), tie-break priority, tie ranks, no randomness.
- `test_engine.py` — end-to-end incl. **G001–G011 golden regression** with the
  M1 oracle-contract mapper (eligible / scheme_ids order / status), overall
  statuses, response structure, provenance, JSON serialization, determinism,
  input validation, KB invariants.

Golden fixtures are consumed from `KB/normalized/golden_fixtures.json` (the M1
regression oracle) — the engine reproduces every expected verdict and the
**ranked order** of `scheme_ids`.

## 18. Design Decisions & Open Questions

Resolved (this session, engine-level):
1. **Activity early-gate** — business + activity ∉ taxonomy ⇒ UNSUPPORTED_ACTIVITY,
   no recommendations (G007); supported-but-unmapped activities still evaluate.
2. **Purpose → candidates** — business ⇒ MFS/TL/AMY/UNY, education ⇒ ELS,
   unknown ⇒ insufficient info. ELS is never a business candidate.
3. **Scoring semantics** — N/A factor = 100 w/ weight (truthful), partner
   UNAVAILABLE = 0 w/ weight (ceiling 85), UNKNOWN = 50, unverified activity = 80.
4. **Tie-break** — score → eligibility → financial → activity → KB order; ties
   share ranks. Reproduces golden ordering exactly.
5. **Inclusivity** — null flags default inclusive; explicit `false` = strict.
6. **Pure dataclasses**, no pydantic; `dataclass_to_dict` for serialization.
7. **`course_family` authoritative for coverage** — listed ⇒ covered; not listed
   ⇒ NO_MATCH; unresolvable raw course ⇒ UNKNOWN (never fabricated).

Open / deferred (deliberately out of M2 scope):
- Real partner master (SCA/SFB/NBFC-MFI availability, fund utilization) — requires
  the M1 approved partner-PDF ingestion gate.
- Exact PRD "score 94" hero numbers are UI-facing; the engine exposes factor
  scores and ranking, the frontend renders its own numbers if desired.
- Location/geo partner routing, multi-language strings, FastAPI `POST
  /api/recommend` binding — later milestones (frontend/backend).

## 19. Acceptance Criteria Checklist

- [x] Deterministic, explainable, provenance-preserving engine; same input →
  same output (tested).
- [x] No LLM, no fabricated facts, no KB writes; rule/data duplication avoided.
- [x] UNKNOWN ≠ FAIL everywhere; gap detection from structured results.
- [x] 12 golden fixtures: 11 verdicts (G001–G011) reproduce expected
  eligible/order/status; G012 conditional resolutions unit-tested.
- [x] RecommendationResponse carries reasons, warnings, sources, missing
  information, verification status, factor breakdown, disclaimer.
- [x] Full pytest suite green: `python -X utf8 -m pytest intelligence/tests`.
- [x] Guardrails (partner UNAVAILABLE, exclusivity flags, UNVERIFIED surfaced)
  enforced and tested.