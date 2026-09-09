# SIH26092 — M2 FINAL REPORT (INTELLIGENCE ENGINE)

**Delivered:** 2026-09-09 · **Milestone:** M2 INTELLIGENCE ENGINE · **Status: COMPLETE**
**Verification:** `python -X utf8 -m pytest intelligence/tests` → **139 passed, 1 skipped (G012 unit-covered in matching), 0 failed** · KB/normalized byte-unchanged · no git commits (repo policy)

---

1. **Engine package (`intelligence/`)** — pure-Python, stdlib-only, no pydantic/FastAPI/LLM. Public API: `RecommendationEngine.evaluate(profile, requirement)` → `RecommendationResponse` (JSON-safe via `utils.dataclass_to_dict`).
2. **Components:** `models/` (typed input+result dataclasses, enums/constants incl. frozen weights 0.40/0.25/0.20/0.15 and SCHEME_PRIORITY), `kb/` (loader+repository over `KB/normalized`, read-only; `SIH26092_KB_DIR` override), `normalization/` (INR, profile, activity, education, requirement/purpose), `eligibility/` (operators, OR/AND grouping, evaluator), `matching/` (activity, financial, education, partner), `ranking/` (factor scoring + deterministic tie-break), `explanations/` (reason keys + structured generator), `gaps/` (missing-field detection + aggregation), `engine.py`.
3. **Eligibility:** data-driven evaluation of E001–E006 (E007 EXTERNAL_DOMAIN never gated); scope-aware (ALL_CORE_SCHEMES / SCHEME_GROUP / SCHEME_LIST); grouped rules OR-combined (ENTITY_TYPE_ALLOWED), ungrouped AND-combined; every rule result carries rule id/operator/expected/actual/verdict/reason/sources.
4. **Financial:** KB-driven cost/loan bounds with exact inclusivity (`min_inclusive=false` → strict `>`, TL 1.40L lower bound verified); eligible = 90%×cost capped at loan max; requested-loan check; ELS cap computed from KB formula `min(40L, 90%×course_fee)`; conditional rates/repayment/moratorium resolved only with user context else UNKNOWN.
5. **Activity matching:** 146-activity M1 taxonomy; MATCH/NO_MATCH/UNKNOWN/NOT_APPLICABLE; all mappings UNVERIFIED (DQ-012) preserved and surfaced (factor 80 + warning).
6. **Education matching:** 25 covered families (CF-001..CF-025); covered ⇒ MATCH, non-listed family ⇒ NO_MATCH, unresolvable raw course ⇒ UNKNOWN.
7. **Partner:** UNAVAILABLE for all schemes (M1 partners NOT_INGESTED); score 0, `PARTNER_DATA_UNAVAILABLE`, registered source ids referenced; nothing fabricated.
8. **Scoring/ranking:** 40/25/20/15; N/A factor = 100 (weight retained), partner 0 (ceiling 85), UNKNOWN = 50, unverified activity = 80; tie-break score → eligibility → financial → activity → KB order; exact ties share rank. Score is a matching score, never a probability (disclaimer included).
9. **Explanations + provenance:** stable i18n reason keys (reasons + warnings) and deduplicated SourceRefs (id/title/url/role) per recommendation, built from the decision objects.
10. **Gap detection:** canonical missing fields aggregated (community, annual_family_income, caste_certificate, entity_type, activity, project_cost, education_fee, course) — from structured results, never heuristics; provided-but-unsupported activity is NOT_SUPPORTED, not a gap.
11. **Verification semantics:** UNKNOWN ⇒ UNVERIFIED (never FAIL); tri-state eligible True/None/False reproduced exactly for every golden case.
12. **Golden-fixure regression (12/12):** G001–G011 reproduce the expected eligible / `scheme_ids` (in ranked order) / status from `KB/normalized/golden_fixtures.json`; G012 conditional resolutions covered as unit tests (UNY rate 13/15, TL moratorium by category, ELS repayment 12/10).
13. **Test suite:** 140 checks (139 pass + G012 unit checks in `test_matching.py`); operator truth table, normalization/validation, OR/AND grouping, scopes, boundary inclusivity, ELS formula, conditionals, scoring/tie-break/determinism, response structure, JSON serialization, validation raises, KB invariants.
14. **Docs:** `docs/M2_INTELLIGENCE_ENGINE.md` (19-section design record incl. decisions §18 and acceptance checklist §19), `docs/M2_PROGRESS.md` updated (all milestones DONE), this report.
15. **Open/deferred** (out of M2 scope, deliberate): real partner master (needs M1 partner-PDF ingestion gate), geo-partner routing, FastAPI `/api/recommend` binding, i18n strings.

### Environment
- Python 3.13.3 (Windows), stdlib + pytest. None of `KB/normalized/*` modified (hashes/sizes unchanged); repo has zero git commits (none created).

### Guardrail compliance
- [x] Deterministic (tested byte-identical) · [x] No LLM · [x] No fabricated facts · [x] UNKNOWN ≠ FAIL · [x] No KB writes · [x] Provenance + verification preserved everywhere.