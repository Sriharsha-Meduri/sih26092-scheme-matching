# tests/test_kb_golden.py — SIH26092 KB golden fixture tests + conditional-value oracle checks
# Runs under pytest or directly (python tests/test_kb_golden.py).
# The oracle below is a MINIMAL deterministic evaluator over validated KB facts. It is NOT the
# production Intelligence Engine (M2); it exists so the KB test fixtures encode the expected
# behaviour the real engine must reproduce.
import io, os, sys, json, unittest

KB_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def load(name):
    with open(os.path.join(KB_ROOT, 'normalized', name), encoding='utf-8') as f:
        return json.load(f)

def as_dict(records):
    return {r['id']: r for r in records}

SCHEMES = None
RULES = None
FPS = None
ACTIVITIES = None
ACT_MAP = None
EDU = None
SOURCES = None

def _init():
    global SCHEMES, RULES, FPS, ACTIVITIES, ACT_MAP, EDU, SOURCES
    SCHEMES = as_dict(load('schemes.json')['records'])
    RULES = as_dict(load('eligibility_rules.json')['records'])
    FPS = as_dict(load('financial_parameters.json')['records'])
    ACTIVITIES = as_dict(load('activities.json')['records'])
    ACT_MAP = load('activity_scheme_mappings.json')
    EDU = load('education.json')
    SOURCES = as_dict(load('sources.json')['records'])

INCOME_SCHEMES = ['NSFDC-MFS', 'NSFDC-TL', 'NSFDC-AMY', 'NSFDC-UNY']
ALL_SCHEMES = INCOME_SCHEMES + ['NSFDC-ELS']

def resolve_conditional(value, profile):
    """Evaluate a conditional_value or formula against a profile; scalars pass through."""
    if isinstance(value, dict) and value.get('type') == 'conditional':
        for branch in value['branches']:
            when = branch['when']
            if '==' in when:
                if profile.get(when_culprit_key(when)) == when['==']:
                    return branch['value']
            elif 'IN' in when:
                if profile.get(when_culprit_key(when)) in when['IN']:
                    return branch['value']
            elif 'NOT_IN' in when:
                if profile.get(when_culprit_key(when)) not in when['NOT_IN']:
                    return branch['value']
        return None
    return value

def when_culprit_key(when):
    if '==' in when:
        return 'repayment_has_started' if isinstance(when['=='], bool) else None
    if 'IN' in when:
        vals = when['IN']
        if any('Small Finance Banks' in v for v in vals):
            return 'channel_type'
        if any('Co-operative' in v for v in vals):
            return 'channel_type'
        return 'activity_category'
    if 'NOT_IN' in when:
        return 'activity_category'
    return None

def els_cap(profile):
    fp = FPS['FP-NSFDC-ELS-011']
    cap = fp['value']
    fee = profile.get('course_fee')
    if fee is None:
        return None, None
    percent = next(t for t in cap['terms'] if t['kind'] == 'percent_of')
    const = next(t for t in cap['terms'] if t['kind'] == 'const')
    return min(const['value'], (percent['percent'] / 100.0) * fee), const['value']

def activity_in_taxonomy(name):
    return any(r['name'] == name for r in ACTIVITIES.values())

def evaluate(profile):
    """Return {'eligible': bool|None, 'scheme_ids': [...], 'status': str}."""
    activity = profile.get('activity')
    if activity and not activity_in_taxonomy(activity):
        return {'eligible': None, 'scheme_ids': [], 'status': 'NOT_SUPPORTED'}

    statuses = {}
    for sid in ALL_SCHEMES:
        statuses[sid] = _scheme_status(sid, profile)

    passing = [s for s, v in statuses.items() if v == 'PASS']
    unknown = [s for s, v in statuses.items() if v == 'UNKNOWN']
    if passing:
        return {'eligible': True, 'scheme_ids': passing, 'status': 'VERIFIED'}
    if unknown:
        return {'eligible': None, 'scheme_ids': [], 'status': 'UNVERIFIED'}
    return {'eligible': False, 'scheme_ids': [], 'status': 'VERIFIED'}

def _scheme_status(sid, profile):
    income = profile.get('annual_family_income')
    community = profile.get('community')
    cert = profile.get('caste_certificate')
    # All-core rules E001/E002/E003
    if community is not None and community != 'Scheduled Caste (SC)':
        return 'FAIL'
    if cert is False:
        return 'FAIL'
    if income is None:
        return 'UNKNOWN'
    if income > 500000:
        return 'FAIL'

    if sid == 'NSFDC-ELS':
        cf = profile.get('course_family')
        if cf is None:
            return 'UNKNOWN'
        families = {c['family'] for c in EDU['course_families']}
        if cf not in families:
            return 'FAIL'
        fee = profile.get('course_fee')
        if fee is None:
            return 'UNKNOWN'
        cap, _ = els_cap(profile)
        if cap is None:
            return 'UNKNOWN'
        return 'PASS'

    entity = profile.get('entity_type')
    if entity is None:
        return 'UNKNOWN'
    if entity not in ('Individual', 'Partnership Firm', 'Co-operative Society'):
        return 'FAIL'

    sch = SCHEMES[sid]
    cost = profile.get('project_cost')
    if cost is None:
        return 'UNKNOWN'
    cb = sch['cost_bounds']
    if cb['min'] is not None:
        ok = cost > cb['min'] if cb['min_inclusive'] is False else cost >= cb['min']
        if not ok:
            return 'FAIL'
    if cb['max'] is not None and cost > cb['max']:
        return 'FAIL'
    loan_max = sch['loan_bounds']['max']
    fin = sch['financing_percent']
    loan = min((fin / 100.0) * cost, loan_max) if loan_max is not None else (fin / 100.0) * cost
    if loan < 0:
        return 'FAIL'
    return 'PASS'