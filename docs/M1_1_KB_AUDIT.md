# SIH26092 — M1.1 Knowledge Base Audit

Status: COMPLETE. Audit only — no KB/data files created, modified, renamed, or deleted.

Reference documents read this session:
- docs/ps.md
- docs/prd.md
- docs/M0_ARCHITECTURE.md
- docs/M0_DATA_MODEL.md
- docs/M0_COMPONENT_CONTRACTS.md
- docs/M0_DECISIONS.md

Source files audited (READ-ONLY):
- KB/Master DB.txt
- KB/SIH26092_Knowledge_Base_Source_Register.xlsx
- KB/SIH26092_Scheme_Master_KB.json

---

## 1. Top-level entities/categories currently present

### JSON (`KB/SIH26092_Scheme_Master_KB.json`)
Top-level keys (8):
`retrieved_on`, `organization`, `source_of_truth`, `schemes`, `eligibility_rules`, `els_course_types`, `activities`, `sources`

Entities (logical): scheme (5), eligibility_rule (7), els_course (25), activity (148), source (9).

### XLSX (`KB/SIH26092_Knowledge_Base_Source_Register.xlsx`)
Two worksheets:
- `Source Register` — provenance register; 6 columns × 33 data rows across 10 categories.
- `Current Scheme Snapshot` — 8 columns × 5 data rows (human-readable summary of the 5 schemes).

### TXT (`KB/Master DB.txt`)
- 0 bytes, 0 lines. Contains no entities, no fields, no records.

## 2. Fields available for each entity

### Scheme (JSON, 17 fields per record)
`scheme_id`, `scheme_name`, `scheme_type`, `purpose`, `project_cost_min_inclusive`, `project_cost_max`, `max_loan_amount`, `financing_percent`, `nsfdc_rate_percent`, `beneficiary_rate_percent`, `repayment_years`, `moratorium_months`, `installment_frequency`, `channel_types`, `target_group`, `application_mode`, `notes`

### Eligibility rule (JSON, 6 positional fields per tuple)
`[id, scope, field, operator, value, explanation]`

### els_course (JSON, 1 field per entry)
free-text course-family string (25 entries)

### activity (JSON, 1 field per entry)
free-text activity name string, grouped by sector key

### source (JSON, 6 positional fields per tuple)
`[id, name, url, authority_flag, focus, retrieved_on]`

### Excel Snapshot scheme (8 columns)
`Scheme | Purpose | Project/Course limit | Financing | Beneficiary interest | Repayment/Moratorium | Channel | Source`

### Excel Source Register row (6 columns)
`Category | Document / Source | Format | Authority | URL | Use in Knowledge Base`

## 3. Number of records per entity

| Entity | Count |
|---|---|
| schemes | 5 |
| eligibility_rules | 7 |
| els_course_types | 25 |
| activities | 148 (Agricultural & Allied 20; Small Industries 51; Service & Transport 77) |
| sources | 9 |
| Excel Source Register rows | 33 |
| Excel Snapshot rows | 5 |
| Master DB.txt records | 0 |

## 4. The five schemes and their IDs

| ID | Name |
|---|---|
| NSFDC-MFS | Micro Finance Scheme (MFS) |
| NSFDC-TL | Term Loan (TL) |
| NSFDC-AMY | Aajeevika Micro-Finance Yojana (AMY) |
| NSFDC-UNY | Udyam Nidhi Yojana (UNY) |
| NSFDC-ELS | Educational Loan Scheme (ELS) |

Scheme IDs exist only in JSON. Excel/imply by name; PRD example response uses `NSFDC-TL` (matches JSON IDs).

## 5. All eligibility rules and their IDs

| ID | Scope | Field | Operator | Value |
|---|---|---|---|---|
| E001 | All NSFDC credit/loan schemes | Community | must_be | Scheduled Caste (SC) |
| E002 | All NSFDC credit/loan schemes | Income | less_than_or_equal | ₹5,00,000 annual family income |
| E003 | All NSFDC credit/loan schemes | Caste certificate | required | Valid certificate from competent authority |
| E004 | Income-generating activities | Entity type | allowed | Individual |
| E005 | Income-generating activities | Entity type | allowed | Partnership Firm |
| E006 | Income-generating activities | Entity type | allowed | Co-operative Society |
| E007 | Skill Development Training | Income | no_ceiling | None |

Observations:
- E002 effective date `2026-01-07` is buried inside the explanation string.
- Rules are scoped by free-text strings, NOT by scheme_id (per-scheme application is not explicit).
- E007 references "Skill Development Training" — a domain NOT among the 5 schemes (scope question, see §15).
- Only 5 operators used: `must_be`, `less_than_or_equal`, `required`, `allowed`, `no_ceiling`. No `unit` or `priority` fields.

## 6. All activities and their sectors

3 sectors (148 total):
- **Agricultural & Allied Sector** (20): Agricultural Land Purchase, Hatcheries, Duckery, Goat Rearing, Sheep Farming, Fisheries, Ornamental Fish Rearing, Tractors, Power Tillers, Cultivation & Processing of Medicinal Plants, Honey Bee Cultivation, Irrigation Borewells/Minor Irrigation, Agricultural Implements, Horticulture, Sericulture, Layers / Broilers, Cows / Buffaloes, Piggery, Aquaculture, Floriculture
- **Small Industries Sector** (51): Automobile Repair / Servicing Units, Brick Making, Bicycle Repairing Shops, Bicycle Seat Cover Making, Biogas Plant, Candle Manufacturing, Car Upholstery & Seat Making, Cement Solid Blocks, Coir Industry, Carpet Manufacturing, Copperware/Utensils Manufacturing, Exercise Books & Registers Making, Readymade Garment Manufacturing, Ginger & Turmeric Processing, Granite Tiles, Handmade Paper, Ornaments Polishing Units, Stone Crushing, Supari Processing, Printing Press, Furniture Making, Flour Mill, Soft Toys Making, Handlooms/Powerlooms, Embroidery/Knitting, Woollen Garments/Shawls Making etc., Hosiery Units, Jute Fabrics/Bags, Leather Garments, Leather Processing, Leather & Rexine Articles, Lime Kilns, Plastic Bags Manufacturing, Potteries, Handicrafts Making, Pouch Making, Powerlooms, Incense Stick Making, Rubber Industry, Shoe/Chappal Manufacturing, Umbrella Making, Fiberglass Manufacturing, Mineral Water Bottling Plant, Oil Mills, Saw Mills, Footwear Manufacturing, Soft/Stuffed Toys Making, Silver Ornaments Making, Bakery, Bamboo Furniture Making, Battery Making
- **Service & Transport Sector** (77): Departmental Stores, Beautician, Band Party, Fish/Meat Shops, Petty Shops, Bicycle Repairing Shops, Diagnostic Center / Blood Bank, Book Binding/Book Shops, Cards Shop, Clinical Labs, Stationery Shops, Cloth Merchant, Computer Centres, Computer Hardware & Servicing, Dental Clinics, Desktop Printing, Driving School, Eye Clinics, Food Packing Unit, Gas Agency, Gem Stone Cutting & Polishing, Photography/Videography, Shopping Complex, Shuttering, Spice Grinding, Spray Painting, Silk Weaving, Steel Fabrication, Sweet Shop, Tailoring, Water Sports Equipments, Chemist Shops, Wooden/Steel Furniture, Dhabas/Mini Hotels, Tourist Lodge, Automobile Repairs, Electrical Items Shop, Hardware Shop, Electrical Winding, Welding & Refrigeration, Vegetable Vending, Watch Repair/Sales Shop, Bangle/Cosmetic Shop, Digital Mixing Lab, Seeds/Fertilizers/Pesticides Shops, Auto Rickshaws/Auto Load Carrier, Light Commercial Vehicles/Mini Buses, Jeeps/Car Taxies, Earth Movers (JCB) etc., Laundry/Dry-cleaning Shops, Machine Shops, Marble Polishing, Milk Chilling Centres/Booths, Garments Shop, Mobile Crane, Nursing Home/Hospitals, Nursery School, Passenger/Fishing Boats, Public Address System, Pump Set/Minor Irrigation, Ropeway, Sales & Servicing of Electric Items, Saw Mills, Supplying Unit, Commercial Centre (STD/Photocopier/Scanner), Seeds & Pesticides Shops, Tannery, Tent House/Decorators, Transport Vehicles (Autos, Taxies, LCVs, Buses, Trucks), Travel Agency, TV/Audio-Video/Refrigerator/AC Repair, Typing School, Tyre Retreading, Tyre Servicing & Vulcanising, Xerox/Typing/Lamination Centre, Internet Cafe, Cable TV

"Tailoring" (used in PRD hero demo) IS present in Service & Transport. No activity→scheme linkage exists.

## 7. Education/course-family information

ELS (`NSFDC-ELS`): purpose "Regular full-time professional/technical recognized courses in India or abroad"; target_group "Eligible Scheduled Caste students"; channel "Channelizing Agencies (CAs) / applicable banks under ELS arrangement"; application "PM-SURAJ online portal or applicable channel".

`els_course_types` (25 flat strings):
1. Engineering (Diploma / B.Tech / B.E / M.Tech / M.E)
2. Architecture (B.Arch / M.Arch)
3. Medical (MBBS / MD / MS)
4. Biotechnology / Microbiology / Clinical Technology
5. Pharmacy (B.Pharma / M.Pharma)
6. Dental (BDS / MDS)
7. Physiotherapy (B.Sc / M.Sc)
8. Pathology (B.Sc / M.Sc)
9. Nursing (B.Sc / M.Sc)
10. Information Technology (BCA / MCA)
11. Management (BBA / MBA)
12. Hotel Management & Catering Technology
13. Law (LLB / LLM)
14. Education (CT / NTT / B.Ed / M.Ed)
15. Physical Education (C.PEd / B.PEd / M.PEd)
16. Journalism & Mass Communication
17. Geriatric Care
18. Midwifery
19. Laboratory Technician
20. Chartered Accountancy (CA)
21. Cost Accountancy (ICWA)
22. Company Secretaryship (CS)
23. Actuarial Sciences
24. AMIE / Institute of Electronics & Telecommunication
25. Higher Education: Doctoral Studies leading to M.Phil / PhD from recognized institutions

No course→scheme link, no course-duration, no fee data, no institution-list, no course-level eligibility differentiation.

## 8. All source/provenance information

### JSON `sources` (9, all retrieved_on 2026-09-08)
| ID | Name | URL | Authority flag | Focus |
|---|---|---|---|---|
| S001 | NSFDC current Credit/Loan Schemes page | nsfdc.nic.in/scheme | Primary/current | Scheme financial parameters; ELS course list |
| S002 | NSFDC FAQ | nsfdc.nic.in/faqs | Primary/current | Eligibility, 5 schemes, application, channel, prudential norms |
| S003 | NSFDC Eligibility Requirements | nsfdc.nic.in/eligibility-requirements | Primary/current | General eligibility and entity conditions |
| S004 | NSFDC Indicative Activities | nsfdc.nic.in/indicative-activities | Primary/current | Activity/business taxonomy |
| S005 | NSFDC How to Apply | nsfdc.nic.in/how-to-apply-2 | Primary/current | Application flow |
| S006 | NSFDC Forms | nsfdc.nic.in/form | Primary/current | TL and ELS downloadable forms |
| S007 | NSFDC Channel Partners | nsfdc.nic.in/our-channel-partners | Primary/current | Partner categories + lists |
| S008 | NSFDC Lending Policies & Refinance | nsfdc.nic.in/information-disclosed-on-own-initiative | Primary/current | Lending policy documents |
| S009 | NSFDC Compendium of Schemes | nsfdc.nic.in/UploadedFiles/.../1-4-1.pdf | Secondary/historical | Historical descriptions; version-check |

Top-level JSON also carries `retrieved_on: 2026-09-08` and `source_of_truth: https://nsfdc.nic.in/scheme`.

### Excel Source Register (33 rows, all Authority="Primary")
Categories: 01_Core (4), 02_Activities (1), 03_Application (1), 04_Partners (8), 05_Operations (2), 06_LendingPolicy (4), 07_GovContext (5), 08_Evidence (4), 09_Documents (3), 10_Stories (1).

Notable rows: 38 SCAs PDF, 11 PSBs PDF, RRBs PDF, NBFC-MFIs PDF, Other & SIDBI PDF, SFB PDF, Co-op Societies PDF; "State/Agency Utilisation as of 31 Jul 2026" PDF; Performance Data hub; 4 lending-policy PDFs; 4 PIB press releases (incl. FY2025-26 ₹775.26 cr / 59,002 beneficiaries); PM-DAKSH / PM-AJAY / SCDC context pages.

No published_date/effective_date anywhere. No per-fact provenance attached to any scheme/rule/activity.

## 9. Structured vs free-text

| Data | Type |
|---|---|
| Scheme IDs, numeric financial fields | STRUCTURED (but see §10/§14 for type violations) |
| eligibility_rules tuple fields (id, field, operator, value) | STRUCTURED (scope + explanation are free-text) |
| els_course_types entries | FREE-TEXT |
| activity names | FREE-TEXT (no ids, no aliases, no sub_sector) |
| sources tuples | STRUCTURED (authority flag + focus are free-text) |
| Scheme `notes` | FREE-TEXT (contains rule semantics: ELS cap, TL 12-month moratorium, rate layering) |
| Excel Snapshot cells | FREE-TEXT prose |
| Excel register | STRUCTURED columns, free-text descriptions |

## 10. Duplicate / inconsistent records

- Duplicate activities (exact, cross-sector): "Bicycle Repairing Shops", "Saw Mills" — each in Small Industries AND Service & Transport.
- Near-duplicates/semantic overlaps: "Powerlooms" vs "Handlooms/Powerlooms"; "Seeds/Fertilizers/Pesticides Shops" vs "Seeds & Pesticides Shops"; "Shoe/Chappal Manufacturing" vs "Footwear Manufacturing"; "Automobile Repair / Servicing Units" vs "Automobile Repairs"; "Pump Set/Minor Irrigation" vs "Irrigation Borewells/Minor Irrigation"; "Photography/Videography" vs "Desktop Printing" (overlap unclear).
- Inconsistent naming: mixed casing ("Goat Rearing" vs "Cows / Buffaloes"), "etc." suffixes ("Woollen Garments/Shawls Making etc.", "Earth Movers (JCB) etc.").
- MFS vs AMY: identical project_cost_max (140,000) and max_loan_amount (125,000); differ only in rate (6.5 vs 15) and channel (SCA/CA vs NBFC-MFI). Overlap is real; not evidence of error.
- Scheme field-name inconsistency vs PRD schema: `project_cost_min_inclusive`/`financing_percent`/`nsfdc_rate_percent`/`beneficiary_rate_percent`/`repayment_years`/`moratorium_months` vs PRD `project_cost_min`/`financing_percentage`/`nsfdc_interest_rate`/`beneficiary_interest_rate`/`repayment_period`/`moratorium_period`.
- ELS `max_loan_amount` (4,000,000) equals `project_cost_max` (4,000,000) despite `financing_percent` 90 — internally inconsistent with a pure 90% formula (see §14).

## 11. Missing fields required by PS/PRD

### Scheme (PRD §10.1, 22 fields) vs JSON (17)
MISSING: `id`, `status`, `effective_from`, `effective_until`, `source_id`, `created_at`, `updated_at`.
RENAMED: `scheme_name`→`name`, `project_cost_min_inclusive`→`project_cost_min`, `financing_percent`→`financing_percentage`, `nsfdc_rate_percent`→`nsfdc_interest_rate`, `beneficiary_rate_percent`→`beneficiary_interest_rate`, `repayment_years`→`repayment_period`, `moratorium_months`→`moratorium_period`.
JSON-only extras: `channel_types`, `notes` (keep — prd §8 narrative mentions channel types).

### Eligibility rule (PRD §10.2, 11 fields) vs JSON (6)
MISSING: `scheme_id` (have string `scope`), `unit`, `priority`, `source_id`, `effective_from`, `effective_until`.

### Activity (PRD §10.3: id, name, sector, sub_sector, keywords, aliases)
MISSING: `id`, `sub_sector`, `keywords`, `aliases`. Have only `name` (sector is the JSON grouping key).

### Partner (PRD §10.4, 14 fields)
MISSING entirely: `id, partner_id, name, partner_type, state, district, address, latitude, longitude, phone, email, website, status, source_id`. Only `channel_types` (category-level) in scheme records; partner PDF URLs in Excel.

### Other PRD entities absent from KB
- `scheme_partner_mapping` — MISSING
- `partner_performance` — MISSING (only utilisation PDF URL)
- `application_requirements` — MISSING (document checklist)
- `faqs` structured — MISSING (URL only)
- `sources` per-fact provenance — PARTIAL (document-level only)

### Excel Snapshot missing vs JSON
`scheme_id`, `nsfdc_rate_percent`, `installment_frequency`, `application_mode`, `target_group`, eligibility rules, ELS course list, full activity list, per-source focus/dates. (Snapshot is a summary — fine.)

## 12. Data required by the future Intelligence Engine but currently unavailable

1. Activity→scheme mapping — required for PRD reason "Tailoring is an eligible activity" and the 25% Activity Match factor. NOT PRESENT.
2. Per-scheme eligibility scope — rules scoped to strings, not scheme_id; cannot evaluate per-scheme without interpretation.
3. Normalized financial values — UNY beneficiary rate and ELS repayment/moratorium are strings; not directly evaluable.
4. Explicit lower-bound semantics — `project_cost_min_inclusive` null for 4 schemes; TL uses `140000.01`.
5. Financial-feasibility inputs — ELS cap needs course-fee input (user-supplied per B7); rule semantics of the cap are in free-text `notes`.
6. Status + effective dates — no scheme/rules status or effective windows (only E002 date in text).
7. Per-fact provenance — no source_id on schemes/rules/activities.
8. Activity alias/keyword data — free-text matching needed for "tailoring" etc.; no aliases (e.g., "garment making").
9. Partner master + coordinates — routing cannot operate.
10. Partner performance/availability — routing factor 20%/15% cannot operate.
11. Document requirements — P1 checklist output impossible.
12. Golden test fixtures — no fixtures exist (M1.3 scope).
13. i18n reason keys — no explanation-key catalog (M1 later).

## 13. Source conflicts

1. **Compendium authority.**
   SOURCE A (JSON S009): `"Secondary/historical"`.
   SOURCE B (Excel 01_Core): `Authority = Primary`.
   STATUS: Needs verification (M0 B1 — recommend Secondary).
2. **Interest-rate ranges.**
   SOURCE A (PS): "typically ranging from 6.5% to 8% per annum".
   SOURCE B (JSON/Excel): AMY = 15% beneficiary; UNY = 13/15%.
   STATUS: Needs verification — PS wording may be illustrative; UI must show real per-scheme rates with source.
3. **Term Loan lower bound.**
   SOURCE A (JSON): `project_cost_min_inclusive: 140000.01`.
   SOURCE B (Excel/PS): "> ₹1.40 lakh".
   STATUS: Needs verification of inclusive/exclusive semantics (M0 B2 — recommend exclusive).
4. **ELS terms representation.**
   SOURCE A (JSON): "12 if repayment has not started; 10 if repayment has started" and "Course period + 1 year ... / up to 6 months if ...".
   SOURCE B (Excel/PS): "Up to 10-12 years" and "3 to 12 months" / "Up to 10-12 years depending on status".
   STATUS: Needs verification of exact conditional semantics.
5. **E002 effective date** `2026-01-07` — inside explanation text; source page (S002/S003) not dated in JSON.
   STATUS: Needs verification whether this is a policy-change date.
6. **Channel coverage claims.**
   SOURCE A (PS): "over 100 Channel Partners".
   SOURCE B (Excel register): 38 SCAs + 11 PSBs + RRBs + NBFC-MFIs + SFBs + Co-ops + Other/SIDBI (counts by category).
   STATUS: Compatible but not verifiable from repo content (PDFs not downloaded).

## 14. Suspicious values / boundary cases

- `project_cost_min_inclusive: 140000.01` on TL — float with paise precision in an INR field; encoding hack for "exclusive"; must become an explicit inclusive flag.
- ELS `max_loan_amount = 4,000,000 = project_cost_max`, financing 90% → implies 90% of 4,000,000 = 3,600,000; if the cap is "₹40L or 90% of course fee, whichever is less", then a ₹40L loan requires a fee ≥ ₹44.44L — but project_cost_max is ₹40L. Internal tension requiring verification.
- `financing_percent = 90` constant across all 5 schemes — uniform, consistent with PS "up to 90%", low risk.
- `beneficiary_rate_percent` for UNY is a channel-dependent string ("13 (Co-op Banks/Societies); 15 (SFBs)") — must be modeled as conditional rate, not scalar.
- `installment_frequency: null` for ELS — acceptable (course-length dependent), must be documented.
- No scheme has `project_cost_min_inclusive` except TL — lower bounds otherwise undefined (treat as open/0).
- MFS vs AMY full parameter overlap — only rate+channel differ; recommend UI disambiguation.
- ELS repayment "12 if not started; 10 if started" — repayment window depends on user state; needs conditional modeling.
- ELS "Course period + 1 year" moratorium — course duration is not in KB; needs user input or course-family assumption.

## 15. Information that must NOT be inferred without authoritative evidence

- Activity→scheme eligibility (e.g., whether "Tailoring" is eligible under MFS, TL, both, or neither) — must come from scheme docs + S004 Indicative Activities.
- Threshold semantics at ₹1.40L (≥ vs >) — M0 B2 pending official verification.
- Whether MFS and AMY are direct substitutes or have distinct applicant restrictions.
- UNY channel-dependent rate applicability rules.
- ELS applicability to part-time/distance courses — purpose says "Regular full-time", but this is an unverified keystone.
- "Competent authority" for the caste certificate (E003).
- The 90%-of-course-fee math inputs for ELS cap (actual course fee).
- Whether PM-SURAJ is the sole application route or SCA/CA offline route has identical terms.
- E007 scope (Skill Development Training) relevance — a domain outside the 5 schemes; do not assume it informs loan eligibility.
- The ₹5,00,000 income ceiling's rural/urban uniformity claim (E002 explanation asserts both).

## KB vs M0 data model / PRD — summary

- M0_DATA_MODEL inventory is CONFIRMED with corrections: activities = 148 (not ~154); Excel `04_Partners` = 8 rows; `Master DB.txt` empty.
- All 5 "AVAILABLE" items remain available (partial typing unchanged).
- All "MISSING" items remain missing (partners, mapping, performance, application_requirements, geography, faqs).
- P0/P1 gaps from M0_DATA_MODEL §6 align with this audit §11/§12.

---

## M1.1 STATUS: COMPLETE

## M1.2 recommended scope (Knowledge Base implementation — data only, no product code)
1. Define canonical scheme + rule + activity + source schemas per DOCS_M0 and PRD §10 (typed fields, explicit bound flags, unit annotations).
2. Normalize the 5 schemes: resolve UNY rate, ELS repayment/moratorium/cap into structured conditionals; replace `140000.01` with explicit inclusive=false.
3. Normalize E001–E007 into per-scheme rules with operator vocabulary, unit, priority, explanation, source_id, effective dates; resolve E002 date.
4. Build activity taxonomy: dedupe (Bicycle Repairing Shops, Saw Mills), normalized casing, ids, aliases/keywords, sub_sector.
5. Build activity→scheme matrix (verify against authoritative scheme docs — do not infer).
6. Extend source register: per-fact provenance wiring; resolve Compendium conflict (B1); add published/effective/retrieval timestamps.
7. Download (read-only snapshots into data/) the partner + utilisation PDFs referenced in the Excel register to de-risk R1.
8. Create golden test fixtures (PRD §24: entrepreneur ₹3L tailoring / ₹3.5L income → NSFDC-TL; B.Tech education; ineligible applicant; partner routing).
9. Define validation constraints + a source-conflict flagging procedure.
10. Record all newly-derived values as DERIVED with provenance; never silently overwrite the read-only KB masters.