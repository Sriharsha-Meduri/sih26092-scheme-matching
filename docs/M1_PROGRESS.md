# M1 Progress Log — SIH26092 Knowledge Base

Status ledger updated at every milestone checkpoint. Final state also summarized
in `docs/M1_KNOWLEDGE_BASE.md`.

| Milestone | Status | Output | Notes |
|---|---|---|---|
| M1.1 KB Audit | COMPLETE | `docs/M1_1_KB_AUDIT.md` | 148 activities, 5 schemes, 7 rules, 25 courses, 9 sources. Identified all open data-quality flags. |
| M1.2 Canonical schema | COMPLETE | `KB/schemas/` (16 files + README.md) | 15 schemas incl. golden_fixture; all pass `check_schema`; cross-file `$ref` resolution OK. Raw snapshots created in `KB/raw/` with SHA-256 manifest. `scheme`/`eligibility_rule`/`financial_parameter`/`sector`/`activity`/`activity_scheme_mapping`/`education`/`document_requirement`/`source`/`provenance`/`data_quality_issue`/`partner`/`golden_fixture`/`index` + `kb_defs`. |
| M1.3 Scheme normalization | COMPLETE | `KB/normalized/schemes.json` | 5 schemes canonicalized: explicit cost/loan bounds (+`min_inclusive=false` for TL), status_assumption (derived), channel_types as arrays, education marker. |
| M1.4 Eligibility normalization | COMPLETE | `KB/normalized/eligibility_rules.json` | E001–E007 preserved; machine operators `== <= EXISTS IN NO_CEILING`; scope objects (ALL_CORE_SCHEMES / SCHEME_GROUP / EXTERNAL_DOMAIN); E002 effective_from `2026-01-07`; E007 flagged EXTERNAL_DOMAIN (DQ-007); E004–E006 group `ENTITY_TYPE_ALLOWED`. |
| M1.5 Financial parameter normalization | COMPLETE | `KB/normalized/financial_parameters.json` | 51 params (10/scheme + ELS loan_cap_formula). Conditionals: UNY rate 13/15 (channel), ELS repayment 12/10, ELS moratorium (course-period/bool), TL moratorium 6/12. No EMI. |
| M1.6 Activity taxonomy + mapping | COMPLETE | `KB/normalized/activities.json`, `sectors.json`, `activity_scheme_mappings.json` | 148 raw entries → 146 unique activities (exact dup `Bicycle Repairing Shops`+`Saw Mills` merged, both sectors kept). 3 sectors. 146 activity mappings — ALL UNVERIFIED inheritance (DQ-012). |
| M1.7 Education knowledge | COMPLETE | `KB/normalized/education.json` | 25 course families CF-001..CF-025 with parsed levels (derived); ELS education_eligibility summary (E001/E002/E003 + course-coverage). |
| M1.8 Provenance + source layer | COMPLETE | `KB/normalized/sources.json`, `provenance.json` | 34 sources (S001–S009 from JSON + register merge; S010–S034 Excel-only). S009 authority CONFLICTED (JSON Secondary/historical vs Excel Primary, DQ-008), not resolved. Record-level edges auto-generated from each entity's `sources`; field-level edges for every derived/conditional fact. |
| M1.9 Partner knowledge | COMPLETE (stub) | `KB/normalized/partners.json` | NOT_INGESTED; gap documented; 13 registered source ids (partner/ops/lending-policy). No fabricated partner facts. Routing = Developer 2. |
| M1.10 Data quality + validation | COMPLETE | `KB/tools/validate_kb.py` + `KB/tools/check_schemas.py` | 13 DQ issues (DQ-001..DQ-013). Validation: schema-integrity + referential integrity + raw SHA-256. Passes. |
| M1.11 Golden fixtures | COMPLETE | `KB/normalized/golden_fixtures.json` + `KB/tests/` | 12 fixtures (G001–G012) incl. PRD hero (G001), income boundary (G002/G003), loan boundary (G004/G005), multiple/no match, missing input, education, conditional oracle. 20 tests pass (build determinism, validation, fixtures, conditionals, S009 conflict). |
| M1.12 Documentation + handoff | COMPLETE | `docs/M1_KNOWLEDGE_BASE.md` | 18-section handoff doc written. |

## Raw-source integrity (checked at every milestone)
Verified at every checkpoint: `Master DB.txt` 0 B · `Source Register.xlsx` 10 776 B · `Scheme Master KB.json` 13 546 B. SHA-256 registered in `KB/normalized/index.json`; validation re-verifies hashes on every run.

## Milestone detail notes
- M1.2 note: schemas validate per-record (envelopes `{'entity','records'}`); single-document files (education, provenance, mappings, partners, document_requirements, index) validate as a whole.
- M1.3 note: `scheme.moratorium` is conditional for ELS and TL; `rates.beneficiary` conditional for UNY; all in `derived_fields`.
- M1.5 note: ELS cap formula = `min(₹40L, 90% × course_fee)` (DQ-005 tension with `max_loan_amount = project_cost_max = ₹40L`).
- M1.6 note: activity→scheme policy is explicit — taxonomy membership is NOT a verified eligibility fact; mappings are UNVERIFIED with inherit_sector=true (see M2 verification ticket).
- M1.8 note: Excel register has 33 data rows; JSON adds S006 (NSFDC Forms) with no register row → category null. Merge by URL.
- M1.11 note: `KB/tools/overlays/golden_fixtures.json` is the curation source; build copies it to normalized.

## Open items for M2 + humans
1. Approve official-PDF partner download + ingestion (partner master). (Human gate.)
2. Resolve Compendium authority conflict DQ-008 (M0 B1 recommends Secondary/historical).
3. Resolve TL bound semantics DQ-001 (M0 B2 recommends exclusive — already modeled exclusive).
4. Verify E002 effective date and UNY/ELS conditional rates against policy PDFs (S019-S022).
5. Per-activity eligibility verification (all 146 activity mappings are UNVERIFIED).
6. ELS course-duration/moratorium inputs (user-supplied per M0 B7).

---

# M1 FINAL REPORT

**Delivered:** 2026-09-09 · **Status: COMPLETE** · Raw artifacts byte-unchanged · 20/20 tests passing · validation green.

1. **Files created/modified in M1:** `docs/M1_PROGRESS.md`, `docs/M1_KNOWLEDGE_BASE.md`, `KB/raw/` (3 snapshots + README), `KB/schemas/` (15 schemas + README), `KB/normalized/` (12 entity files + index.json), `KB/tools/` (build_kb.py, validate_kb.py, check_schemas.py), `KB/tools/overlays/` (curation.json, golden_fixtures.json), `KB/tests/` (3 test modules). No original raw files modified (sizes/hashes verified: 0 B / 10 776 B / 13 546 B).
2. **Schemes:** 5 (`NSFDC-MFS`, `NSFDC-TL`, `NSFDC-AMY`, `NSFDC-UNY`, `NSFDC-ELS`); explicit cost/loan bounds, conditional rates/moratorium, `status_assumption` marked derived.
3. **Eligibility rules:** 7 (E001–E007) with machine operators `== <= EXISTS IN NO_CEILING`; scheme-aware scopes; E007 EXTERNAL_DOMAIN (context-only, DQ-007); E002 effective_from 2026-01-07 (derived).
4. **Financial parameters:** 51 (10/scheme + ELS cap formula). Conditionals: UNY rate 13/15, ELS repayment 12/10, ELS moratorium, TL moratorium 6/12. No EMI.
5. **Activities:** 148 raw entries → 146 unique in 3 sectors (20/51/77); exact duplicates merged with both sector memberships (Bicycle Repairing Shops, Saw Mills → DQ-013).
6. **Activity→scheme mappings:** 146 records, ALL `UNVERIFIED`, `inherit_sector=true`; policy note forbids treating taxonomy membership as verified eligibility (DQ-012). 3 sector-level mappings.
7. **Education:** 25 course families (CF-001..CF-025); levels parsed where parenthesised (derived); ELS education_eligibility summary.
8. **Sources:** 34 (S001–S009 JSON+register merged by URL; S010–S034 Excel-only). S006 category null. **Conflict:** S009 `CONFLICTED` (Secondary/historical vs Primary — both preserved, DQ-008).
9. **Provenance:** record-level edges for all schemes/rules/activities/sectors/course-families/FPs (auto-generated, roles PRIMARY/CORROBORATING) + 6 curated field-level edges covering every derived/conditional/conflicting fact.
10. **Partner status:** NOT_INGESTED; stub with gap description + 13 registered source ids; no fabricated facts; routing = Developer 2.
11. **Data-quality registry:** 13 issues (DQ-001..DQ-013); 8 WARNING + 5 INFO; severities/resolutions recorded.
12. **Validation:** `validate_kb.py` green (schemas OK, per-record schema validation, referential integrity, raw SHA-256 match). `check_schemas.py` green.
13. **Golden fixtures:** 12 (G001–G012) covering PRD hero, income boundary (at/above), TL bound (exclusive + loan), multi/no match, unsupported activity, non-SC, missing input, education covered/non-covered, conditional oracle.
14. **Tests:** 20/20 passed (build determinism, validation, 11 fixture verdicts, 5 conditional resolutions, raw integrity).
15. **Conflicts carried (not resolved):** S009 authority; TL ₹1.40L boundary semantics (modeled exclusive per M0 B2, human confirm open); UNY/ELS conditional terms wording; ELS ₹40L/90% cap tension (DQ-005); E002 date.
16. **Gaps:** partner master; per-scheme document checklists (only caste certificate verified); per-activity eligibility; ELS course-duration input; `Master DB.txt` empty.
17. **Human-verification values:** TL bound exclusive 140000; UNY 13/15; ELS 12/10 + moratorium branches; ELS cap formula min(40L,90%); TL moratorium 6/12; E002 2026-01-07; MFS/AMY cap inclusiveness (`up to` per Snapshot); status ACTIVE_ASSUMED.
18. **Consumption guidance:** §16 of `docs/M1_KNOWLEDGE_BASE.md` (read path, hardcode-avoidance, eligibility evaluation, derived/UNVERIFIED handling, UI source citation).
19. **Next milestone:** M2 Intelligence Engine — implement golden-fixture oracle semantics, per-activity + conditional-value verification tickets, partner ingestion (after human gate).