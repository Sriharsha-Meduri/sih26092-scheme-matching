# SIH26092 — M2 Intelligence Engine — Progress Log

**Project:** SIH26092 · **Milestone:** M2 INTELLIGENCE ENGINE · **Owner:** Knowledge/D1 team
**Read first:** `docs/M0_ARCHITECTURE.md`, `docs/M0_COMPONENT_CONTRACTS.md`, `docs/M0_DECISIONS.md`, `docs/M1_KNOWLEDGE_BASE.md`, `docs/M2_INTELLIGENCE_ENGINE.md`
**KB contract:** `KB/normalized/*` (frozen M1). **Statuses below are updated after each milestone checkpoint.**

---

## Milestone tracker

| ID | Milestone | Status |
|---|---|---|
| M2.1 | Input contract (canonical typed models) | DONE |
| M2.2 | Deterministic normalization | DONE |
| M2.3 | Eligibility engine (data-driven rules) | DONE |
| M2.4 | Activity matching (preserves UNVERIFIED) | DONE |
| M2.5 | Financial fit (inclusive/exclusive + ELS formula) | DONE |
| M2.6 | Education matching | DONE |
| M2.7 | Partner fit (no fabrication) | DONE |
| M2.8 | Candidate generation (deterministic) | DONE |
| M2.9 | Scoring (40/25/20/15) | DONE |
| M2.10 | Structured explanation engine | DONE |
| M2.11 | Gap / missing-information detection | DONE |
| M2.12 | Final result model + public engine entry | DONE |
| M2.13 | Golden fixtures (12/12) + full test suite + docs | DONE |

## Checkpoint log

- **M2.1–M2.13 (session close):** full engine implemented in `intelligence/`
  (models, kb, normalization, eligibility, matching, ranking, explanations,
  gaps, engine) with **139 passing tests (140 with G012 conditional unit
  coverage), 1 intentionally skipped**. All 11 eligible/ineligible golden
  scenarios reproduce the M1 verdicts (G001–G011) including the ranked
  `scheme_ids` order; G012 conditional resolutions (UNY rate 13/15 by channel,
  TL moratorium by activity category, ELS repayment branch) are covered as unit
  tests. M2 docs written (see `docs/M2_INTELLIGENCE_ENGINE.md` for the 19-section
  design record and `docs/M2_FINAL_REPORT.md` for the milestone summary).

## Open decisions (engine-level)

Recorded in `docs/M2_INTELLIGENCE_ENGINE.md` §18. All were resolved this session:
- Activity early-gate: `business` purpose + activity not in taxonomy → overall
  `UNSUPPORTED_ACTIVITY`, no recommendations (G007).
- Purpose → candidates: business → MFS/TL/AMY/UNY; education → ELS.
- Scoring semantics: N/A factor scores 100 with weight retained; partner
  UNAVAILABLE scores 0 with weight retained (max achievable 85); UNKNOWN factor
  scores 50; UNVERIFIED activity mapping scores 80.
- Tie-break order: score desc → eligibility → financial → activity → KB scheme
  order. Ranks may tie intentionally.
- Inclusivity: `min_inclusive=false`/`max_inclusive=false` = strict; null = inclusive.

## Constraints (M2, per master prompt)

- Read KB dynamically; never duplicate government rules in Python.
- UNKNOWN != FAIL. Missing input never becomes a rejection.
- Never fabricate partners/rates/URLs. Preserve provenance + verification status.
- Deterministic: same KB + same input → same decision, score, order, reasons.
- No LLM in the decision path. No FastAPI/frontend in M2. No writes to `KB/`.