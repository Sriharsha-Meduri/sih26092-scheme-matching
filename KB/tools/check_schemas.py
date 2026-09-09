import io, sys, json, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from jsonschema import RefResolver, Draft7Validator

base = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'schemas'))
schemas = {}
for p in glob.glob(os.path.join(base, '*.schema.json')):
    with open(p, 'r', encoding='utf-8') as f:
        s = json.load(f)
    if '$id' not in s:
        print('MISSING $id:', os.path.basename(p)); continue
    schemas[s['$id']] = (p, s)
print('loaded', len(schemas), 'schemas')

from urllib.parse import urljoin
from pathlib import Path
import urllib.request, urllib.parse

base_uri = Path(base).absolute().as_uri() + '/'
ok = True
for idname, (p, s) in schemas.items():
    try:
        Draft7Validator.check_schema(s)
    except Exception as e:
        ok = False; print('INVALID SCHEMA', idname, e); continue
    r = RefResolver(base_uri=base_uri, referrer=s)
    def walk(node):
        global ok
        if isinstance(node, dict):
            if '$ref' in node:
                try:
                    r.resolve(node['$ref'])
                except Exception as e:
                    print('UNRESOLVED $ref', node['$ref'], 'in', idname, '->', e); ok = False
            for x in node.values(): walk(x)
        elif isinstance(node, list):
            for x in node: walk(x)
    walk(s)

also = [n for n in os.listdir(base) if n.endswith('.schema.json')]
missing = [n for n in also if n not in schemas]
print('files found in dir:', len(also), '| loaded:', len(schemas), '| unloaded:', missing)
print('ALL OK' if ok else 'ISSUES FOUND')