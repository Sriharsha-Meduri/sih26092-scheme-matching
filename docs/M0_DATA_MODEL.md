# SIH26092 — M0 Data Model (FROZEN)

Status: FROZEN (M0). KB files are read-only during M0. M1 implements normalization.

## 1. Current Knowledge Base Inventory (verified)

| Item | Status | Notes |
|---|---|---|
| 5 schemes (MFS, TL, AMY, UNY, ELS) | AVAILABLE | JSON `schemes`; Excel snapshot agrees |
| Eligibility rules (E001–E007) | AVAILABLE (partial typing) | string scope, not per-scheme |
| Financial parameters | AVAILABLE (partial typing) | UNY rate & ELS terms stored as strings |
| Activities (~154, 3 sectors) | AVAILABLE (denormalized) | duplicates, mixed casing, no ids |
| ELS course types (25) | AVAILABLE (flat strings) | no course↔scheme link |
| Sources (S001–S009) | AVAILABLE (document-level) | no per-fact provenance |
| Partner data | MISSING | only category-level channel_types + PDF URLs |
| scheme↔partner mapping | MISSING | |
| partner_performance | MISSING | only "State/Agency Utilisation" PDF URL |
| application_requirements | MISSING | |
| Geography / coordinates | MISSING | |
| faqs (structured) | MISSING | URL only |
| Master DB.txt | MISSING (empty file) | no content |

## 2. Entities Identified (logical, for M1)

- scheme
- eligibility_rule
- activity
- activity_scheme_map
- els_course
- partner
- scheme_partner_mapping
- partner_performance
- application_requirement
- source (provenance)
- faq
- golden_scenario

## 3. Conceptual Field Normalization (current → target)

| JSON current | Target (logical) |
|---|---|
| project_cost_min_inclusive | project_cost_min + explicit inclusive/exclusive bound |
| project_cost_max | project_cost_max |
| max_loan_amount | max_loan_amount |
| financing_percent | financing_percentage |
| nsfdc_rate_percent | nsfdc_interest_rate |
| beneficiary_rate_percent | beneficiary_interest_rate |
| repayment_years | repayment_period + unit |
| moratorium_months | moratorium_period + unit |
| installment_frequency | installment_frequency (nullable) |
| channel_types | channel_types (category-level) |
| target_group | target_group |
| application_mode | application_mode |
| notes (ELS cap / 12-mo condition) | structured caps + condition handles |

### Untyped values to resolve in M1
- UNY beneficiary_rate: channel-dependent (co-op 13% / SFB 15%)
- ELS repayment & moratorium: repayment-state-dependent
- ELS cap: min(₹40L, 90% of course fee) — needs user-supplied course-fee input
- TL lower bound: `project_cost_min_inclusive: 140000.01` encodes "exclusive" — must be made explicit

## 4. Provenance Model (PRD §9)
Every important fact: source_id, source_url, authority, published_date, effective_date, retrieval_timestamp, version. Fact-level granularity, applied during M1.

## 5. Known Conflicts (needs verification — do NOT resolve silently)
1. Compendium of Schemes: JSON says "Secondary/historical"; Excel says "Primary".
2. PS rate range (6.5–8%) vs AMY (15%) and UNY (13/15%).
3. TL lower-bound encoding (140000.01) vs "> ₹1.40 lakh" prose.
4. ELS terms string-form vs simplified "10–12 years / 3–12 months".
5. E002 effective date 2026-01-07 (inside explanation string).

## 6. Data Gaps Priority
### P0 (M1 scope)
- activity→scheme mapping
- normalized per-scheme eligibility rules
- typed financial parameters
- per-fact provenance
- minimal partner master + scheme_partner_mapping
- golden test fixtures (PRD §24 scenarios)

### P1 (M1/M2)
- partner_performance seed
- application_requirements (document checklist)
- faqs structured
- activity aliases / dedupe
- ELS course detail + fee handling
- i18n keys (EN/HI/TE)

### P2
- RAG index
- geo enrichment (lat/lng for all partners)
- adjacent MoSJE schemes (optional)
- dashboards / analytics

## 7. M1 Scope (implement at M1, not now)
- Canonical scheme schema
- Normalize the 5 schemes
- Normalize eligibility rules E001–E007
- Build activity taxonomy (dedupe, ids, aliases)
- Build activity→scheme matrix
- Validate/add authoritative sources
- Fill missing scheme information
- Wire provenance
- Define validation constraints
- Create golden test data (entrepreneur, education, ineligible, partner routing)