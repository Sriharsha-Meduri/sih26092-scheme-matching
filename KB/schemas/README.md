# KB/schemas — Canonical KB Schema (M1.2)

This directory defines the canonical schema for the SIH26092 Knowledge Base.
Every file under `KB/normalized/` must validate against the matching schema here.
Validation is executable: `KB/validation/` (M1.10) runs `jsonschema` over the whole
normalized KB using these schemas.

## Layout
| File | JSON Schema for |
|---|---|
| `kb_defs.schema.json` | Shared definitions (`id`, `source_ref`, `conditional_value`, `availability`, `derived_marker`) referenced by all other schemas via `$ref` (`relative` refs are resolved against the `KB/schemas/` directory). |
| `index.schema.json` | `KB/normalized/index.json` — the KB envelope: version, generated date, source snapshot checksums, entity table of contents, entity counts, notes. |
| `scheme.schema.json` | One NSFDC scheme record (`schemes.json`). |
| `eligibility_rule.schema.json` | One eligibility rule (`eligibility_rules.json`). |
| `financial_parameter.schema.json` | One monetary/timing parameter (`financial_parameters.json`). |
| `sector.schema.json` | One activity sector/segment (`sectors.json`). |
| `activity.schema.json` | One eligible activity (`activities.json`). |
| `activity_scheme_mapping.schema.json` | Activity/sector-to-scheme eligibility mapping (`activity_scheme_mappings.json`). |
| `education.schema.json` | ELS course families + education-eligibility summary (`education.json`). |
| `document_requirement.schema.json` | Document checklists / requirements (`document_requirements.json`). |
| `source.schema.json` | Normalized source registry entry (`sources.json`). |
| `provenance.schema.json` | Record-level and field-level provenance edges (`provenance.json`). |
| `data_quality_issue.schema.json` | Registered data-quality issue / conflict (`data_quality_issues.json`). |
| `partner.schema.json` | Partner master stub — defined now, records empty until partner data is ingested (`partners.json`). |
| `golden_fixture.schema.json` | One golden fixture case (`golden_fixtures.json`, M1.11). |

## Entity definitions
- **Scheme** — a lending programme NSFDC offers. Stable ID is the raw id (`NSFDC-MFS`, `NSFDC-TL`, `NSFDC-AMY`, `NSFDC-UNY`, `NSFDC-ELS`). Carries cost/loan bounds, financing percent, rates, repayment/moratorium, channels, education marker.
- **EligibilityRule** — a single machine-checkable condition derived from the source rule language. Stable IDs E001–E007 preserved. `scope` is explicit (Scheme-list/group/external), `operator` is machine (`==`, `<=`, `IN`, …), `raw_operator` keeps the original wording.
- **FinancialParameter** — one named monetary/timing value of a scheme. IDs `FP-<scheme>-<nnn>`. `value_original` preserves the verbatim source text; `derived` marks computed fields.
- **Sector** — the activity taxonomy segment (Agricultural & Allied, Small Industries, Service & Transport). IDs `SECTOR-AGR`, `SECTOR-SII`, `SECTOR-STT`.
- **Activity** — a discrete eligible activity. Stable IDs `ACT-001…ACT-148`. `source_name` = verbatim authoritative wording; `name` = cleaned display form (formatting only). No meaning is invented.
- **ActivitySchemeMapping** — the bridge between the activity taxonomy and scheme eligibility. Only the source-level statement (“activities under the sector segments”) is VERIFIED; per-activity claims are UNVERIFIED until individually confirmed (ticket for M2/Gemini verification). This schema **forbids** silently turning taxonomy membership into eligibility.
- **EducationEligibility / CourseFamily** — ELS course list parsed into 25 families; `levels` are parsed (derived=true) for later verification.
- **DocumentRequirement** — documents proven required (caste certificate via E003); per-scheme checklists are otherwise NOT_SPECIFIED.
- **Source** — normalized entry of `KB/raw/SIH26092_Knowledge_Base_Source_Register.xlsx` + the JSON `sources` block. Authority-level conflicts are carried, never resolved.
- **Provenance** — who supports each record/fact, and in what role (PRIMARY/CORROBORATING/CONFLICTING).
- **DataQualityIssue** — every known hazard (`FORMAT_HAZARD`, `VALUE_SUSPICIOUS`, `SOURCE_CONFLICT`, `INTERNAL_TENSION`, …) with severity and human-decision resolution status.
- **Partner** — stub only. Partner master data has not been ingested into M1 (see M1.9). Routing is Developer 2.
- **GoldenFixture** — a tested input→expected-output case (M1.11).

## Field semantics (norms)
- **IDs** — stable, unique within entity. Scheme/rule/activity IDs keep the source id where one existed.
- **Units** — INR for money, percent for rates, years/months for duration unless the field name says otherwise.
- **`null`** semantics — a `null` value means **“the source does not provide this, and we will not guess.”** It is deliberately different from `NOT_SPECIFIED` (used when the source actually says something is not covered), from an empty array, and from `UNKNOWN` (used when even existence is uncertain). See `availability`.
- **`availability`** — `AVAILABLE` source states it; `PARTIAL` weaker form stated; `MISSING` no source gives it (hold null); `NOT_SPECIFIED` source explicitly leaves it uncovered; `UNKNOWN` unsure it exists at all.
- **`derived`** / **`derived_fields`** — every computed/interpreted/parsed value is flagged `derived=true` and listed in the record `derived_fields` so downstream (M2) treats it as a verification ticket.
- **Conditional values** — represented as `{"type":"conditional","variable":...,"branches":[{"when":{...},"value":...}]}` (`schema_or_conditional` in `kb_defs`). Used for UNY rate (`13`/`15` by channel) and ELS repayment (`12`/`10` by repayment started?) and ELS moratorium. The supply chain may discover one global rule still exists inside the ORIGINAL static scope string that the doc says “turn INTO a combined field group” — a static vector here instead.

## Relationships
```
Source ──────────────┬── proves ──▶ all entities (source_ref list)
DataQualityIssue ────┴── flags ───▶ any entity
Scheme ──1..N──▶ EligibilityRule (scope)
Scheme ──1..N──▶ FinancialParameter
Sector ──1..N──▶ Activity
Activity/Sector —▶ ActivitySchemeMapping —▶ Scheme
Scheme(ELS) ──▶ EducationEligibility ──▶ CourseFamily
Record/Field ──▶ Provenance edges (source_id + role)
```

## Null/unknown/derived quick rules for contributors
1. Never put a number we do not have. Use `null` + `availability=MISSING`.
2. Never state eligibility we did not verify. Use mapping status UNVERIFIED + inherit_sector=true.
3. Never resolve a source conflict silently. Register a `DataQualityIssue` and keep both values in provenance.
4. Every important claim needs at least one Source id in `sources` or a provenance edge.
5. Parsed numbers from textual strings are derived (`derived=true`), e.g. `level` parsing, and boundary extraction (`140000.01 → 140000 exclusive`, DQ-001).