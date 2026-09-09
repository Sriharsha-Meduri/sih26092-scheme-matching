# validate_kb.py — SIH26092 KB validation (M1.10)
# Deterministic checks:
#  1. every schema file is valid JSON Schema (draft-07)
#  2. every normalized/*.json validates against its schema ($ref resolved against KB/schemas/)
#  3. referential integrity (scheme ids, source ids, activity ids, sector ids, fp ids, cf ids)
#  4. raw artifacts byte-match the SHA-256 snapshot registered in index.json
# Exit code 0 = OK, 1 = FAIL.
import io, os, re, sys, json, glob, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from jsonschema import Draft7Validator, RefResolver
from urllib.parse import urljoin
from pathlib import Path

KB = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SCHEMA_DIR = os.path.join(KB, 'schemas')
NORM_DIR = os.path.join(KB, 'normalized')

errors = []

def jload(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

# ---------------------------------------------------------------- schemas
schemas = {}
for p in glob.glob(os.path.join(SCHEMA_DIR, '*.schema.json')):
    try:
        s = jload(p)
    except Exception as e:
        errors.append(f"SCHEMA NOT JSON: {os.path.basename(p)}: {e}")
        continue
    if '$id' not in s:
        errors.append(f"MISSING $id: {os.path.basename(p)}")
        continue
    try:
        Draft7Validator.check_schema(s)
    except Exception as e:
        errors.append(f"INVALID SCHEMA {s['$id']}: {e}")
    schemas[s['$id']] = s

base_uri = Path(SCHEMA_DIR).absolute().as_uri() + '/'

def get_validator(schema):
    return Draft7Validator(schema, resolver=RefResolver(base_uri=base_uri, referrer=schema))

# map normalized file name -> schema id
FILE_SCHEMA = {
    'schemes.json': 'scheme.schema.json',
    'eligibility_rules.json': 'eligibility_rule.schema.json',
    'financial_parameters.json': 'financial_parameter.schema.json',
    'sectors.json': 'sector.schema.json',
    'activities.json': 'activity.schema.json',
    'activity_scheme_mappings.json': 'activity_scheme_mapping.schema.json',
    'education.json': 'education.schema.json',
    'document_requirements.json': 'document_requirement.schema.json',
    'sources.json': 'source.schema.json',
    'provenance.json': 'provenance.schema.json',
    'partners.json': 'partner.schema.json',
    'data_quality_issues.json': 'data_quality_issue.schema.json',
    'golden_fixtures.json': 'golden_fixture.schema.json',
}

# ---------------------------------------------------------------- normalized
norm = {name: jload(os.path.join(NORM_DIR, name)) for name in FILE_SCHEMA
        if os.path.exists(os.path.join(NORM_DIR, name))}

for fname, schema_id in FILE_SCHEMA.items():
    if fname not in norm:
        if fname != 'golden_fixtures.json':  # added at M1.11; not required before that
            errors.append(f"MISSING NORMALIZED FILE {fname}")
        continue
    if schema_id not in schemas:
        errors.append(f"SCHEMA {schema_id} NOT LOADED (referenced by {fname})")
        continue
    v = get_validator(schemas[schema_id])
    data = norm[fname]
    # Normalized files are either (a) envelopes {'entity','records':[...]} whose RECORDS
    # validate against the record schema, or (b) single-document objects (education,
    # provenance, activity_scheme_mappings, partners, document_requirements, index)
    # that validate as a whole against their schema.
    SINGLE_DOC = {
        'education.json', 'provenance.json', 'activity_scheme_mappings.json',
        'partners.json', 'document_requirements.json', 'index.json',
    }
    if fname in SINGLE_DOC:
        items = [data]
    elif isinstance(data, dict) and 'records' in data:
        items = data['records']
    else:
        items = [data]
    for i, rec in enumerate(items):
        errs = sorted(v.iter_errors(rec), key=lambda e: (str(e.path), e.message))
        if errs:
            label = f"{fname}.records[{i}]"
            for e in errs:
                errors.append(f"{label}: {e.message} @ {list(e.path)}")

# ---------------------------------------------------------------- referential integrity
def record_ids(fname, key='records'):
    return {r['id'] for r in norm[fname][key]} if key in norm[fname] else set()

scheme_ids = record_ids('schemes.json')
source_ids = record_ids('sources.json')
activity_ids = record_ids('activities.json')
sector_ids = record_ids('sectors.json')
cf_ids = record_ids('education.json', 'course_families')
dq_ids = record_ids('data_quality_issues.json')

for r in norm['schemes.json']['records']:
    for s in r['sources']:
        if s not in source_ids: errors.append(f"scheme {r['id']} sources refs unknown {s}")
    for d in r['data_quality_issues']:
        if d not in dq_ids: errors.append(f"scheme {r['id']} dq refs unknown {d}")
    if r['education']['is_education_scheme'] and r['education']['course_family_ids']:
        for c in r['education']['course_family_ids']:
            if c not in cf_ids: errors.append(f"scheme {r['id']} course refs unknown {c}")

for r in norm['eligibility_rules.json']['records']:
    for s in r['sources']:
        if s not in source_ids: errors.append(f"rule {r['id']} sources refs unknown {s}")
    for d in r['data_quality_issues']:
        if d not in dq_ids: errors.append(f"rule {r['id']} dq refs unknown {d}")

for r in norm['financial_parameters.json']['records']:
    if r['scheme_id'] not in scheme_ids: errors.append(f"fp {r['id']} scheme unknown {r['scheme_id']}")
    for s in r['sources']:
        if s not in source_ids: errors.append(f"fp {r['id']} sources refs unknown {s}")
    for d in r['data_quality_issues']:
        if d not in dq_ids: errors.append(f"fp {r['id']} dq refs unknown {d}")

for r in norm['activities.json']['records']:
    for sid in r['sector_ids']:
        if sid not in sector_ids: errors.append(f"activity {r['id']} sector unknown {sid}")
    for s in r['sources']:
        if s not in source_ids: errors.append(f"activity {r['id']} sources refs unknown {s}")
    for d in r['data_quality_issues']:
        if d not in dq_ids: errors.append(f"activity {r['id']} dq refs unknown {d}")

for sm in norm['activity_scheme_mappings.json']['sector_mappings']:
    if sm['sector_id'] not in sector_ids: errors.append(f"mapping sector unknown {sm['sector_id']}")
    for s in sm['scheme_ids']:
        if s not in scheme_ids: errors.append(f"mapping sector {sm['sector_id']} scheme unknown {s}")
for am in norm['activity_scheme_mappings.json']['activity_mappings']:
    if am['activity_id'] not in activity_ids: errors.append(f"mapping activity unknown {am['activity_id']}")
    for s in am['scheme_ids']:
        if s not in scheme_ids: errors.append(f"mapping activity {am['activity_id']} scheme unknown {s}")

for rec in norm['sources.json']['records']:
    for d in rec['data_quality_issues']:
        if d not in dq_ids: errors.append(f"source {rec['id']} dq refs unknown {d}")

for rec in norm['provenance.json']['record_level']:
    if rec['source_id'] not in source_ids:
        errors.append(f"provenance rec edge {rec['entity_type']}:{rec['entity_id']} source unknown {rec['source_id']}")
for rec in norm['provenance.json']['field_level']:
    if rec['source_id'] not in source_ids:
        errors.append(f"provenance field edge {rec['entity_type']}:{rec['entity_id']}.{rec['field']} source unknown {rec['source_id']}")
for rec in norm['education.json']['course_families']:
    for s in rec['sources']:
        if s not in source_ids: errors.append(f"course {rec['id']} sources refs unknown {s}")
for rec in norm['document_requirements.json']['records']:
    if rec['status'] == 'VERIFIED' and rec['source'] not in source_ids:
        errors.append(f"doc {rec['id']} source unknown {rec['source']}")
    for sc in rec['scheme_ids']:
        if sc not in scheme_ids: errors.append(f"doc {rec['id']} scheme unknown {sc}")

for rec in norm['partners.json']['registered_sources']:
    if rec not in source_ids: errors.append(f"partners registered source unknown {rec}")

# ---------------------------------------------------------------- raw integrity
raw_by_file = {
    'Master_DB.txt': os.path.join(KB, 'raw', 'Master_DB.txt'),
    'SIH26092_Knowledge_Base_Source_Register.xlsx': os.path.join(KB, 'raw', 'SIH26092_Knowledge_Base_Source_Register.xlsx'),
    'SIH26092_Scheme_Master_KB.json': os.path.join(KB, 'raw', 'SIH26092_Scheme_Master_KB.json'),
}
if 'index.json' in norm:
    for snap in norm['index.json']['source_snapshots']:
        p = raw_by_file.get(snap['file'])
        if not p or not os.path.exists(p):
            errors.append(f"index snapshot file missing {snap['file']}")
            continue
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        if h != snap['sha256']:
            errors.append(f"RAW INTEGRITY FAILED for {snap['file']} (registered {snap['sha256'][:16]} got {h[:16]})")

# ---------------------------------------------------------------- report
if errors:
    print("VALIDATION FAILED (%d issue(s)):" % len(errors))
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("VALIDATION OK:")
print("  schemas:", len(schemas))
print("  normalized files:", len(norm))
print("  schemes:", len(scheme_ids), "| rules:", len(record_ids('eligibility_rules.json')),
      "| fps:", len(record_ids('financial_parameters.json')), "| activities:", len(activity_ids),
      "| sectors:", len(sector_ids), "| sources:", len(source_ids),
      "| course_families:", len(cf_ids), "| dq issues:", len(dq_ids))
print("  raw integrity: OK")