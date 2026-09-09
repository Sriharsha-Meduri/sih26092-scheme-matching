# build_kb.py — Deterministic KB normalizer for SIH26092 (M1)
# Reads ONLY from KB/raw/* + KB/tools/overlays/curation.json; writes KB/normalized/*.
# Idempotent. Never writes/edits KB/raw or the original corpus files.
import io, os, re, sys, json, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import openpyxl

KB = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
RAW = os.path.join(KB, 'raw')
NORM = os.path.join(KB, 'normalized')
OVERLAYS = os.path.join(KB, 'tools', 'overlays')
os.makedirs(NORM, exist_ok=True)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save(name, obj):
    p = os.path.join(NORM, name)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"    wrote {name}")

def sha256_of(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

# ---------------------------------------------------------------- raw inputs
seed = load_json(os.path.join(RAW, 'SIH26092_Scheme_Master_KB.json'))
curation = load_json(os.path.join(OVERLAYS, 'curation.json'))
scheme_overrides = curation['scheme_overrides']
dq_registry = {d['id']: d for d in curation['data_quality_issues']}

# ---------------------------------------------------------------- Excel register
wb = openpyxl.load_workbook(os.path.join(RAW, 'SIH26092_Knowledge_Base_Source_Register.xlsx'), data_only=True)
register_rows = []  # dicts: category, title, format, authority, url, use
for row in wb['Source Register'].iter_rows(values_only=True):
    if not row or row[0] is None:
        continue
    if str(row[0]).strip() == 'Category':
        continue  # header row
    register_rows.append({
        'category': row[0].strip() if row[0] else None,
        'title': (row[1] or '').strip(),
        'format': (row[2] or '').strip() if row[2] else None,
        'authority': (row[3] or '').strip() if row[3] else None,
        'url': (row[4] or '').strip() if row[4] else None,
        'use': (row[5] or '').strip() if row[5] else None,
    })
snapshot_rows = []
for row in wb['Current Scheme Snapshot'].iter_rows(values_only=True):
    if not row or row[0] is None:
        continue
    if str(row[0]).strip() == 'Scheme':
        continue  # header
    snapshot_rows.append([('' if c is None else str(c)) for c in row])

FMT_MAP = {'Web': 'Web page', 'PDF': 'PDF', 'Gov release': 'Gov release/pdf', 'Gov release/pdf': 'Gov release/pdf'}

# ---------------------------------------------------------------- sources.json
def excel_row_for_url(url):
    for r in register_rows:
        if r['url'] and url and r['url'].rstrip('/') == url.rstrip('/'):
            return r
    return None

def normify_format(fmt):
    return FMT_MAP.get(fmt, fmt)

sources_records = []
excel_used = set()
# 1) JSON-declared sources keep their ids
for s in seed['sources']:
    sid, name, url, auth_flag, focus, retrieved = s[0], s[1], s[2], s[3], s[4], s[5]
    erow = excel_row_for_url(url)
    category = erow['category'] if erow else None
    if erow:
        excel_used.add(id(erow))
    json_auth = 'PRIMARY_CURRENT' if auth_flag.lower().startswith('primary') else 'SECONDARY_HISTORICAL'
    excel_auth = None
    if erow and erow['authority']:
        excel_auth = 'PRIMARY_CURRENT' if erow['authority'].lower().startswith('primary') else ('SECONDARY_HISTORICAL' if erow['authority'].lower().startswith('secondary') else erow['authority'].upper())
    conflict = None
    if erow and json_auth != excel_auth:
        authority_level = 'CONFLICTED'
        conflict = {'json_snapshot_value': json_auth.replace('_CURRENT','').replace('_HISTORICAL','').title() if json_auth=='SECONDARY_HISTORICAL' else json_auth,
                    'excel_register_value': 'Primary' if excel_auth=='PRIMARY_CURRENT' else excel_auth}
        conflict = {'json_snapshot_value': auth_flag, 'excel_register_value': erow['authority']}
    else:
        authority_level = json_auth
    publisher = 'NSFDC' if ('nsfdc.nic.in' in url) else None
    sources_records.append({
        'id': sid,
        'title': erow['title'] if erow else name,
        'category': category,
        'authority_level': authority_level,
        'authority_level_conflict': conflict,
        'publisher': publisher,
        'url': url,
        'format': normify_format(erow['format']) if erow and erow['format'] else ('PDF' if url.endswith('.pdf') else 'Web page'),
        'publication_date': None,
        'retrieved_date': retrieved,
        'notes': erow['use'] if erow else focus,
        'data_quality_issues': ['DQ-008'] if sid == 'S009' else [],
    })

# 2) Excel-only rows get fresh ids S010...
next_id = 10
for r in register_rows:
    if id(r) in excel_used:
        continue
    sid = f"S{next_id:03d}"
    next_id += 1
    sources_records.append({
        'id': sid,
        'title': r['title'],
        'category': r['category'],
        'authority_level': 'PRIMARY_CURRENT' if r['authority'] and r['authority'].lower().startswith('primary') else ('SECONDARY_HISTORICAL' if r['authority'] and r['authority'].lower().startswith('secondary') else (r['authority'] or 'PRIMARY_CURRENT')),
        'authority_level_conflict': None,
        'publisher': 'NSFDC' if (r['url'] and 'nsfdc.nic.in' in r['url']) else None,
        'url': r['url'],
        'format': normify_format(r['format']),
        'publication_date': None,
        'retrieved_date': None,
        'notes': r['use'],
        'data_quality_issues': ['DQ-010'] if r['category'] in ('04_Partners', '05_Operations', '06_LendingPolicy') else [],
    })

source_by_id = {s['id']: s for s in sources_records}
save('sources.json', {'entity': 'source', 'count': len(sources_records), 'records': sources_records})

# ---------------------------------------------------------------- helper builds
SECTOR_KEYS = ['Agricultural & Allied Sector', 'Small Industries Sector', 'Service & Transport Sector']
SECTOR_IDS = ['SECTOR-AGR', 'SECTOR-SII', 'SECTOR-STT']
INCOME_SCHEMES = ['NSFDC-MFS', 'NSFDC-TL', 'NSFDC-AMY', 'NSFDC-UNY']

def channel_split(ch):
    if not ch or ch is None:
        return None
    return [x.strip() for x in ch.split('/ ') if x.strip()]

# ---------------------------------------------------------------- schemes.json
course_ids = []
scheme_records = []
for sch in seed['schemes']:
    sid = sch['scheme_id']
    ov = scheme_overrides.get(sid, {})
    is_els = sid == 'NSFDC-ELS'

    cost_min = ov.get('project_cost_min')
    if cost_min:
        cb_min, cb_min_inc = cost_min['value'], cost_min['inclusive']
        cb_avail = 'PARTIAL'
        cb_note = cost_min['interpretation']
    else:
        cb_min, cb_min_inc = None, None
        cb_avail = 'PARTIAL'
        cb_note = 'no project-cost lower bound specified in source'
    cb_max = sch['project_cost_max']
    cb_max_inc = None

    ben_rate = ov.get('beneficiary_rate')
    repayment = ov.get('repayment')
    moratorium = ov.get('moratorium_months_conditional') or ov.get('moratorium')

    scheme = {
        'id': sid,
        'scheme_name': sch['scheme_name'],
        'short_name': sid.split('-')[1],
        'scheme_type': sch['scheme_type'],
        'purpose': sch['purpose'],
        'cost_bounds': {
            'min': cb_min,
            'min_inclusive': cb_min_inc,
            'max': cb_max,
            'max_inclusive': cb_max_inc,
            'availability': cb_avail,
        },
        'loan_bounds': {
            'min': None,
            'max': sch['max_loan_amount'],
            'availability': 'PARTIAL',
        },
        'financing_percent': sch['financing_percent'],
        'rates': {
            'nsfdc': sch['nsfdc_rate_percent'],
            'beneficiary': ben_rate if ben_rate else sch['beneficiary_rate_percent'],
        },
        'repayment': repayment if repayment else sch['repayment_years'],
        'moratorium': moratorium if moratorium else sch['moratorium_months'],
        'installment_frequency': sch['installment_frequency'],
        'channel_types': channel_split(sch['channel_types']) or [],
        'target_group': sch['target_group'],
        'application_mode': sch['application_mode'],
        'status': None,
        'status_assumption': {
            'assumed_status': 'ACTIVE_ASSUMED',
            'derived': True,
            'basis': f"Scheme listed as current NSFDC scheme on S001 (retrieved {seed['retrieved_on']}); seed has no explicit status field.",
        },
        'education': {
            'is_education_scheme': is_els,
            'course_family_ids': None,
            'eligibility_status': 'NOT_SPECIFIED',
        },
        'notes': sch['notes'],
        'derived_fields': ['status_assumption', 'cost_bounds', 'loan_bounds', 'short_name'],
        'data_quality_issues': list(dict.fromkeys(
            (cost_min or {}).get('data_quality_issues', []) + (['DQ-005'] if is_els else [])
        )),
        'sources': ['S001', 'S002'],
    }
    if cb_min and cb_max and cb_max is not None and not is_els:
        if cb_note:
            scheme['data_quality_issues'] = list(dict.fromkeys(scheme['data_quality_issues'] + ['DQ-001'] if sid == 'NSFDC-TL' else scheme['data_quality_issues']))
    if ben_rate:
        scheme['derived_fields'].append('rates.beneficiary')
    if repayment:
        scheme['derived_fields'].append('repayment')
    if moratorium:
        scheme['derived_fields'].append('moratorium')
    if sid == 'NSFDC-TL' and cb_note:
        scheme['data_quality_issues'] = list(dict.fromkeys(scheme['data_quality_issues'] + ['DQ-001']))
    if sid == 'NSFDC-UNY':
        scheme['data_quality_issues'] = list(dict.fromkeys(scheme['data_quality_issues'] + ['DQ-002']))
    if sid == 'NSFDC-ELS':
        scheme['data_quality_issues'] = list(dict.fromkeys(scheme['data_quality_issues'] + ['DQ-003', 'DQ-004']))
        course_ids = [f"CF-{i:03d}" for i in range(1, len(seed['els_course_types']) + 1)]
        scheme['education'] = {
            'is_education_scheme': True,
            'course_family_ids': course_ids,
            'eligibility_status': 'PARTIAL',
        }
    scheme_records.append(scheme)

save('schemes.json', {'entity': 'scheme', 'count': len(scheme_records), 'records': scheme_records})

# ---------------------------------------------------------------- eligibility_rules.json
OP_MAP = {'must_be': '==', 'less_than_or_equal': '<=', 'required': 'EXISTS', 'allowed': 'IN', 'no_ceiling': 'NO_CEILING'}
FIELD_MAP = {'Community': 'community', 'Income': 'annual_family_income', 'Caste certificate': 'caste_certificate', 'Entity type': 'entity_type'}

def parse_inr(s):
    m = re.search(r'([\d,]+)', s.replace('\u20b9', '').replace('₹', ''))
    if not m:
        return None, None
    return int(m.group(1).replace(',', '')), 'INR'

rule_records = []
for r in seed['eligibility_rules']:
    rid, rscope, rfield, rop, rval, rexp = r
    scope = curation['rule_scope'][rid]
    val = rval
    unit = None
    if rid == 'E002':
        parsed_num, unit = parse_inr(rval)
        val = parsed_num if parsed_num is not None else rval
    cond_group = 'ENTITY_TYPE_ALLOWED' if rid in ('E004', 'E005', 'E006') else None
    eff_from = '2026-01-07' if rid == 'E002' else None
    scope_rec = {
        'type': scope['type'],
        'schemes': scope['schemes'],
        'scheme_group': scope['scheme_group'],
        'scope_derived': scope['type'] in ('ALL_CORE_SCHEMES', 'EXTERNAL_DOMAIN'),
        'notes': scope['notes'],
    }
    rule_records.append({
        'id': rid,
        'name': f"{rfield}: {rval}" if rval != 'None' else f"{rfield}: no ceiling",
        'scope': scope_rec,
        'field': FIELD_MAP[rfield] if rfield in FIELD_MAP else rfield,
        'operator': OP_MAP[rop],
        'raw_operator': rop,
        'value': val,
        'unit': unit,
        'condition_group': cond_group,
        'explanation': rexp,
        'original_explanation': rexp,
        'priority': None,
        'effective_from': eff_from,
        'effective_until': None,
        'sources': ['S003'] + (['S002'] if rid in ('E001', 'E002') else []),
        'data_quality_issues': ['DQ-006'] if rid == 'E002' else (['DQ-007'] if rid == 'E007' else []),
        'notes': scope['notes'],
    })

save('eligibility_rules.json', {'entity': 'eligibility_rule', 'count': len(rule_records), 'records': rule_records})

# ---------------------------------------------------------------- financial_parameters.json
def fp(scheme_id, parameter, label, value, value_original, ptype, unit, condition, derived, definition, dqs, notes=None):
    return {
        'id': f"FP-{scheme_id}-{len(fp_index[scheme_id]) + 1:03d}" if scheme_id in fp_index else f"FP-{scheme_id}-001",
        'scheme_id': scheme_id,
        'parameter': parameter,
        'parameter_label': label,
        'value': value,
        'value_original': value_original,
        'type': ptype,
        'unit': unit if unit else None,
        'condition': condition,
        'derived': derived,
        'definition': definition,
        'sources': ['S001', 'S002'] if scheme_id != 'NSFDC-ELS' else ['S001', 'S002'],
        'data_quality_issues': dqs or [],
        'notes': notes,
    }

fp_index = {s['id']: [] for s in scheme_records}
financial = []
for sch in scheme_records:
    sid = sch['id']
    ov = scheme_overrides.get(sid, {})
    raw = next(x for x in seed['schemes'] if x['scheme_id'] == sid)
    def add(*a, **kw):
        rec = fp(sid, *a, **kw)
        financial.append(rec)
        fp_index[sid].append(rec)

    # project cost
    cost_ov = ov.get('project_cost_min')
    if cost_ov:
        add('project_cost_min', 'Project cost minimum (exclusive)', 140000, '140000.01',
            'number', 'INR', None, True,
            "Lower bound is STRICT: project cost must exceed Rs 1,40,000 (raw value 140000.01 encodes the exclusive boundary).",
            ['DQ-001'], cost_ov['interpretation'])
    else:
        add('project_cost_min', 'Project cost minimum', None, None, 'number', 'INR', None, False,
            "No lower bound specified in source.", [], 'no lower bound specified')
    add('project_cost_max', 'Project cost maximum', raw['project_cost_max'], str(raw['project_cost_max']),
        'integer', 'INR', None, False, 'Maximum project cost eligible (INR).', [], None)
    add('loan_amount_min', 'Loan amount minimum', None, None, 'integer', 'INR', None, False,
        'No loan floor specified in source.', [], 'no loan floor specified')
    add('loan_amount_max', 'Loan amount maximum', raw['max_loan_amount'], str(raw['max_loan_amount']),
        'integer', 'INR', None, False, 'Maximum loan amount (INR).', (['DQ-005'] if sid == 'NSFDC-ELS' else []), None)
    add('financing_percent', 'Financing percentage', raw['financing_percent'], str(raw['financing_percent']),
        'number', 'percent', None, False, "Share of project cost financed (stated 'up to' in PS; constant 90 in seed).", [], None)
    add('nsfdc_interest_rate', 'NSFDC rate to channel', raw['nsfdc_rate_percent'], str(raw['nsfdc_rate_percent']),
        'number', 'percent', None, False, 'Rate NSFDC charges the channelizing agency.', [], None)
    # beneficiary rate
    ben_ov = ov.get('beneficiary_rate')
    if ben_ov:
        add('beneficiary_interest_rate', 'Beneficiary interest rate (channel-dependent)',
            ben_ov, raw['beneficiary_rate_percent'], 'conditional', 'percent', ben_ov, True,
            "Channel-dependent: 13% via Co-op Banks/Societies; 15% via SFBs.", ['DQ-002'], ben_ov['note'])
    else:
        add('beneficiary_interest_rate', 'Beneficiary interest rate', raw['beneficiary_rate_percent'], str(raw['beneficiary_rate_percent']),
            'number', 'percent', None, False, 'Rate charged to the beneficiary.', [], None)
    # repayment
    rep_ov = ov.get('repayment')
    if rep_ov:
        add('repayment_period_years', 'Repayment period (years)', rep_ov, raw['repayment_years'],
            'conditional', 'years', rep_ov, True, "12 years if repayment has not started; 10 years if it has started.",
            ['DQ-003'], rep_ov['note'])
    else:
        add('repayment_period_years', 'Repayment period (years)', raw['repayment_years'], str(raw['repayment_years']),
            'integer', 'years', None, False, 'Repayment period in years.', [], None)
    # moratorium
    mor_ov = ov.get('moratorium_months_conditional')
    if mor_ov:
        add('moratorium_months', 'Moratorium (months)', mor_ov, str(raw['moratorium_months']),
            'conditional', 'months', mor_ov, True, "6 months standard; 12 months for plantation/construction activities.",
            [], mor_ov['note'])
    elif ov.get('moratorium'):
        add('moratorium_months', 'Moratorium', ov['moratorium'], raw['moratorium_months'],
            'conditional', 'months', ov['moratorium'], True, 'Course period + 1 year if repayment not started; up to 6 months otherwise.',
            ['DQ-004'], ov['moratorium']['note'])
    else:
        add('moratorium_months', 'Moratorium (months)', raw['moratorium_months'], str(raw['moratorium_months']),
            'integer', 'months', None, False, 'Moratorium in months.', [], None)
    # installment frequency
    add('installment_frequency', 'Installment frequency', raw['installment_frequency'], str(raw['installment_frequency']),
        'string', None, None, False, 'Repayment installment cadence; null for ELS (course-length dependent).', [], None)
    # ELS cap formula
    if sid == 'NSFDC-ELS':
        cap = ov['loan_cap_formula']
        add('loan_cap_formula', 'Loan cap formula (ELS)', cap, None,
            'formula', None, None, True, "Lesser of Rs 40 lakh or 90% of course fee.", ['DQ-005'],
            cap['source_note'])

save('financial_parameters.json', {'entity': 'financial_parameter', 'count': len(financial), 'records': financial})

# ---------------------------------------------------------------- sectors + activities
activity_records = {}
sector_activity_ids = {}
act_counter = 0
for skey, sid_key in zip(SECTOR_KEYS, SECTOR_IDS):
    acts = seed['activities'][skey]
    ids = []
    for name in acts:
        key = name.strip()
        if key in activity_records:
            rec = activity_records[key]
            rec['sector_ids'].append(sid_key)
            rec['normalization_notes'] = f"Exact duplicate of source entry across sectors ({', '.join(rec['sector_ids'])}); merged into one canonical activity."
        else:
            act_counter += 1
            ids.append(f"ACT-{act_counter:03d}")
            activity_records[key] = {
                'id': f"ACT-{act_counter:03d}",
                'name': key,
                'source_name': key,
                'sector_ids': [sid_key],
                'aliases': [],
                'normalization_notes': None,
                'sources': ['S004'],
                'data_quality_issues': (['DQ-013'] if key in ('Bicycle Repairing Shops', 'Saw Mills') else []),
            }
        if activity_records[key]['id'] not in ids:
            ids.append(activity_records[key]['id'])
    sector_activity_ids[sid_key] = list(dict.fromkeys(ids))

activities = [activity_records[k] for k in activity_records]
save('activities.json', {'entity': 'activity', 'count': len(activities), 'records': activities})

sectors = []
for skey, sid_key in zip(SECTOR_KEYS, SECTOR_IDS):
    sectors.append({
        'id': sid_key,
        'name': skey,
        'source_name': skey,
        'activity_ids': sector_activity_ids[sid_key],
        'sources': ['S004'],
        'data_quality_issues': [],
    })
save('sectors.json', {'entity': 'sector', 'count': len(sectors), 'records': sectors})

# ---------------------------------------------------------------- activity_scheme_mappings.json
mapping = {
    'entity': 'activity_scheme_mapping',
    'policy': {
        'derivation_note': (
            "NSFDC publishes ONE indicative activity taxonomy (S004) covering its credit schemes. "
            "The corpus does NOT state per-activity or per-scheme eligibility. Sector/activity membership is "
            "therefore mapped to the four income-generating schemes (MFS, TL, AMY, UNY) as UNVERIFIED, "
            "inherit-from-sector relationships. This is an ASSUMPTION, not a verified fact."
        ),
        'verification_note': (
            "Per-activity verification is a follow-on task (M2/Gemini + scheme documents). Until then, "
            "the Intelligence Engine must present activity-based eligibility as provisional and UNVERIFIED "
            "(PRD 40/25/20/15: Activity Match weight must not silently turn into a hard eligibility claim)."
        ),
    },
    'sector_mappings': [
        {
            'sector_id': sid_key,
            'activity_count': len(sector_activity_ids[sid_key]),
            'scheme_ids': list(INCOME_SCHEMES),
            'status': 'UNVERIFIED',
            'evidence': ['S001', 'S004'],
            'derived': True,
            'notes': "Sector treated as indicative coverage for income-generating schemes; not a verified per-activity eligibility statement.",
        }
        for sid_key in SECTOR_IDS
    ],
    'activity_mappings': [
        {
            'activity_id': a['id'],
            'scheme_ids': list(INCOME_SCHEMES),
            'inherit_sector': True,
            'status': 'UNVERIFIED',
            'evidence': ['S001', 'S004'],
            'derived': True,
            'notes': "Inherited from sector-level mapping (UNVERIFIED). Per-activity verification required.",
        }
        for a in activities
    ],
}
save('activity_scheme_mappings.json', mapping)

# ---------------------------------------------------------------- education.json
course_records = []
for i, raw_text in enumerate(seed['els_course_types'], 1):
    raw_text = raw_text.strip()
    m = re.match(r'^(.*?)\s*\((.*)\)\s*$', raw_text)
    if m:
        family = m.group(1).strip()
        levels = [x.strip() for x in m.group(2).split('/')]
        note = None
    else:
        family = raw_text
        levels = []
        note = None
    course_records.append({
        'id': f"CF-{i:03d}",
        'family': family,
        'raw_text': raw_text,
        'levels': levels,
        'level_derived': bool(m),
        'coverage_status': 'LISTED_IN_COVERED_COURSES',
        'notes': note,
        'sources': ['S001'],
    })

education = {
    'entity': 'education',
    'education_eligibility': {
        'scheme_id': 'NSFDC-ELS',
        'summary': (
            "Eligible Scheduled Caste student; annual family income <= Rs 5,00,000 (rural and urban, "
            "effective 2026-01-07 per E002); pursuing a regular full-time professional/technical course "
            "from the NSFDC covered-course list (S001), in India or abroad. Loan: lesser of Rs 40 lakh or "
            "90% of course fee. All course-level expectations beyond the covered list are NOT_SPECIFIED."
        ),
        'general_eligibility': [
            {'rule_id': 'E001', 'field': 'community', 'operator': '==', 'value': 'Scheduled Caste (SC)', 'notes': None},
            {'rule_id': 'E002', 'field': 'annual_family_income', 'operator': '<=', 'value': 500000, 'notes': 'effective 2026-01-07'},
            {'rule_id': 'E003', 'field': 'caste_certificate', 'operator': 'EXISTS', 'value': 'Valid certificate from competent authority', 'notes': None},
            {'rule_id': None, 'field': 'course_family', 'operator': 'IN', 'value': 'nsfdc_els_course_families', 'notes': 'Course must come from the NSFDC covered list (S001).'},
        ],
        'sources': ['S001', 'S003'],
        'data_quality_issues': [],
    },
    'course_families': course_records,
}
save('education.json', education)

# ---------------------------------------------------------------- document_requirements.json
document_requirements = {
    'entity': 'document_requirement',
    'records': [
        {
            'id': 'DOC-001',
            'document': 'SC (Scheduled Caste) certificate from competent authority',
            'scheme_ids': ['NSFDC-MFS', 'NSFDC-TL', 'NSFDC-AMY', 'NSFDC-UNY', 'NSFDC-ELS'],
            'rule_derived': True,
            'mandatory': True,
            'status': 'VERIFIED',
            'source': 'S003',
            'notes': 'Derived from rule E003 (caste certificate required).',
        }
    ],
    'gap_notes': (
        'Exact per-scheme document checklists are NOT_SPECIFIED in the current corpus (DQ-011). '
        'Only the caste certificate is rule-verified. Any P1 checklist output must clearly mark '
        'other documents as indicative until confirmed (recommend: application forms S006 + M2 web verification).'
    ),
}
save('document_requirements.json', document_requirements)

# ---------------------------------------------------------------- provenance.json
record_edges = []
for rec in scheme_records:
    record_edges.append({'entity_type': 'scheme', 'entity_id': rec['id'], 'source_id': 'S001', 'role': 'PRIMARY',
                         'note': 'Financial parameters and scheme facts.'})
    record_edges.append({'entity_type': 'scheme', 'entity_id': rec['id'], 'source_id': 'S002', 'role': 'CORROBORATING',
                         'note': 'FAQ covers five primary schemes; cross-check.'})
for rec in rule_records:
    for i, src in enumerate(rec['sources']):
        record_edges.append({'entity_type': 'eligibility_rule', 'entity_id': rec['id'], 'source_id': src,
                             'role': 'PRIMARY' if i == 0 else 'CORROBORATING',
                             'note': 'Attribution by source-register coverage note, not per-rule citation.'})
for rec in activities:
    record_edges.append({'entity_type': 'activity', 'entity_id': rec['id'], 'source_id': 'S004', 'role': 'PRIMARY', 'note': None})
for rec in sectors:
    record_edges.append({'entity_type': 'sector', 'entity_id': rec['id'], 'source_id': 'S004', 'role': 'PRIMARY', 'note': None})
for rec in course_records:
    record_edges.append({'entity_type': 'course_family', 'entity_id': rec['id'], 'source_id': 'S001', 'role': 'PRIMARY', 'note': None})
for rec in financial:
    record_edges.append({'entity_type': 'financial_parameter', 'entity_id': rec['id'], 'source_id': 'S001', 'role': 'PRIMARY',
                         'note': 'Scheme financial parameters from current scheme page.'})

field_edges = [
    {'entity_type': 'scheme', 'entity_id': 'NSFDC-TL', 'field': 'cost_bounds.min_inclusive', 'source_id': 'S001',
     'role': 'PRIMARY', 'derived': True, 'note': 'Raw 140000.01 parsed as exclusive lower bound; DQ-001.'},
    {'entity_type': 'scheme', 'entity_id': 'NSFDC-ELS', 'field': 'repayment', 'source_id': 'S001',
     'role': 'PRIMARY', 'derived': True, 'note': 'Conditional (12/10) parsed from string; DQ-003. Excel Snapshot corroborates.'},
    {'entity_type': 'scheme', 'entity_id': 'NSFDC-ELS', 'field': 'moratorium', 'source_id': 'S001',
     'role': 'PRIMARY', 'derived': True, 'note': 'Conditional parsed; course-period branch needs user input; DQ-004.'},
    {'entity_type': 'scheme', 'entity_id': 'NSFDC-UNY', 'field': 'rates.beneficiary', 'source_id': 'S001',
     'role': 'PRIMARY', 'derived': True, 'note': 'Channel-dependent 13/15 parsed; DQ-002.'},
    {'entity_type': 'financial_parameter', 'entity_id': 'FP-NSFDC-ELS-011', 'field': 'value', 'source_id': 'S001',
     'role': 'PRIMARY', 'derived': True, 'note': 'Loan cap formula min(40L, 90% course fee); DQ-005.'},
    {'entity_type': 'source', 'entity_id': 'S009', 'field': 'authority_level', 'source_id': 'S009',
     'role': 'CONFLICTING', 'derived': False, 'note': 'JSON snapshot: Secondary/historical. Excel register (01_Core): Primary. DQ-008. NOT resolved.'},
]

provenance = {'entity': 'provenance', 'record_level': record_edges, 'field_level': field_edges}
save('provenance.json', provenance)

# ---------------------------------------------------------------- partners.json (M1.9 stub)
partner_source_ids = [s['id'] for s in sources_records if s['category'] in ('04_Partners', '05_Operations', '06_LendingPolicy')]
partners = {
    'entity': 'partner',
    'ingestion_status': 'NOT_INGESTED',
    'records': [],
    'gap': {
        'description': (
            'Partner master data (SCAs, PSBs, RRBs, NBFC-MFIs, SFBs, Cooperative Societies, Other/SIDBI) '
            'has NOT been parsed into the KB. Only the PDF URLs and coverage notes are registered.'
        ),
        'reason': 'Partner PDFs are referenced in the Source Register but not downloaded/parsed. Content must not be fabricated.',
        'required_action_gate': 'Decide: approve official-PDF download into data/ + parse partner master (recommended next milestone).',
    },
    'registered_sources': partner_source_ids,
    'routing_status': 'NOT_PART_OF_M1 (Developer 2: partner routing uses this KB''s partner data when available).',
}
save('partners.json', partners)

# ---------------------------------------------------------------- data_quality_issues.json
dqs = [dq_registry[d] for d in ['DQ-001', 'DQ-002', 'DQ-003', 'DQ-004', 'DQ-005', 'DQ-006', 'DQ-007', 'DQ-008', 'DQ-009', 'DQ-010', 'DQ-011', 'DQ-012', 'DQ-013']]
save('data_quality_issues.json', {'entity': 'data_quality_issue', 'count': len(dqs), 'records': dqs})

# ---------------------------------------------------------------- golden_fixtures.json (M1.11)
gf = load_json(os.path.join(OVERLAYS, 'golden_fixtures.json'))
gf['entity'] = 'golden_fixture'
gf['count'] = len(gf['records'])
save('golden_fixtures.json', gf)

# ---------------------------------------------------------------- index.json (envelope)
raw_files = {
    'Master_DB.txt': os.path.join(RAW, 'Master_DB.txt'),
    'SIH26092_Knowledge_Base_Source_Register.xlsx': os.path.join(RAW, 'SIH26092_Knowledge_Base_Source_Register.xlsx'),
    'SIH26092_Scheme_Master_KB.json': os.path.join(RAW, 'SIH26092_Scheme_Master_KB.json'),
}
snap = []
for name, p in raw_files.items():
    snap.append({'file': name, 'sha256': sha256_of(p), 'size_bytes': os.path.getsize(p), 'status': 'UNCHANGED'})

index = {
    'kb_name': 'SIH26092 Knowledge Base',
    'kb_version': '1.0.0',
    'generated_by': 'SIH26092 M1 · KB/tools/build_kb.py',
    'generated_on': '2026-09-09',
    'schema_version': '1.0.0',
    'schema_location': 'KB/schemas/',
    'source_snapshots': snap,
    'entities': {
        'schemes': 'schemes.json',
        'eligibility_rules': 'eligibility_rules.json',
        'financial_parameters': 'financial_parameters.json',
        'sectors': 'sectors.json',
        'activities': 'activities.json',
        'activity_scheme_mappings': 'activity_scheme_mappings.json',
        'education': 'education.json',
        'document_requirements': 'document_requirements.json',
        'sources': 'sources.json',
        'provenance': 'provenance.json',
        'partners': 'partners.json',
        'data_quality_issues': 'data_quality_issues.json',
        'golden_fixtures': 'golden_fixtures.json',
    },
    'stats': {
        'schemes': len(scheme_records),
        'eligibility_rules': len(rule_records),
        'financial_parameters': len(financial),
        'sectors': len(sectors),
        'activities_unique': len(activities),
        'activities_raw_entries': sum(len(seed['activities'][k]) for k in SECTOR_KEYS),
        'course_families': len(course_records),
        'sources': len(sources_records),
        'sources_excel_rows': len(register_rows),
        'activity_mappings': len(mapping['activity_mappings']),
        'data_quality_issues': len(dqs),
        'document_requirements': len(document_requirements['records']),
        'partners_ingested': 0,
        'golden_fixtures': gf['count'],
    },
    'notes': (
        'Canonical normalized KB. All content is either (a) directly sourced from the raw artifacts or '
        '(b) explicitly DErived with derived=true and a basis. No government facts were invented. '
        'Activity/scheme mappings are UNVERIFIED by design (see activity_scheme_mappings.json policy). '
        'Partners not ingested (see partners.json gap). See docs/M1_KNOWLEDGE_BASE.md.'
    ),
}
save('index.json', index)

print("BUILD COMPLETE")