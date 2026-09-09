# tests/test_kb_build.py — build determinism + validation smoke test
import os, sys, subprocess, unittest, hashlib
KB_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

PY = [sys.executable]

def run(script):
    return subprocess.run(PY + [script], cwd=KB_ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')

class TestBuild(unittest.TestCase):
    def test_build_is_deterministic(self):
        r1 = run(os.path.join(KB_ROOT, 'tools', 'build_kb.py'))
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        snapshot = {}
        norm = os.path.join(KB_ROOT, 'normalized')
        for f in os.listdir(norm):
            with open(os.path.join(norm, f), 'rb') as fh:
                snapshot[f] = hashlib.sha256(fh.read()).hexdigest()
        r2 = run(os.path.join(KB_ROOT, 'tools', 'build_kb.py'))
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        for f in os.listdir(norm):
            with open(os.path.join(norm, f), 'rb') as fh:
                self.assertEqual(snapshot[f], hashlib.sha256(fh.read()).hexdigest(), f"nondeterministic: {f}")

    def test_validation_passes(self):
        r = run(os.path.join(KB_ROOT, 'tools', 'validate_kb.py'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_raw_sources_unchanged(self):
        sizes = {
            'SIH26092_Scheme_Master_KB.json': 13546,
            'SIH26092_Knowledge_Base_Source_Register.xlsx': 10776,
            'Master DB.txt': 0,
        }
        for name, size in sizes.items():
            p = os.path.join(KB_ROOT, name)  # originals live at KB/ (KB_ROOT == ...\KB)
            self.assertTrue(os.path.exists(p), name)
            if os.path.exists(p):
                self.assertEqual(size, os.path.getsize(p), name)

if __name__ == '__main__':
    unittest.main()