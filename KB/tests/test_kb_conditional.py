import io, sys, os, unittest, json

KB_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_kb_golden as kb

class TestGoldenFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kb._init()
        cls.fixtures = kb.load('golden_fixtures.json')['records']

    def fixture(self, fid):
        return next(f for f in self.fixtures if f['id'] == fid)

    def assert_verdict(self, fid):
        fx = self.fixture(fid)
        verdict = kb.evaluate(fx['input'])
        self.assertEqual(fx['expected']['eligible'], verdict['eligible'], f"{fid} eligible")
        if fx['expected']['eligible'] is None:
            self.assertEqual(fx['expected']['status'], verdict['status'], f"{fid} status")
        else:
            self.assertEqual(set(fx['expected']['scheme_ids']), set(verdict['scheme_ids']),
                             f"{fid} scheme set")

    def test_g001_hero_demo(self):
        self.assert_verdict('G001')

    def test_g002_income_at_ceiling(self):
        self.assert_verdict('G002')

    def test_g003_income_above_ceiling(self):
        self.assert_verdict('G003')

    def test_g004_tl_loan_boundary(self):
        self.assert_verdict('G004')

    def test_g005_tl_exclusive_lower_bound(self):
        self.assert_verdict('G005')

    def test_g006_multiple_match(self):
        self.assert_verdict('G006')

    def test_g007_unsupported_activity(self):
        self.assert_verdict('G007')

    def test_g008_non_sc_applicant(self):
        self.assert_verdict('G008')

    def test_g009_missing_income(self):
        self.assert_verdict('G009')

    def test_g010_education_bt(self):
        self.assert_verdict('G010')

    def test_g011_education_not_covered(self):
        self.assert_verdict('G011')

    def test_fixture_set_complete(self):
        ids = {f['id'] for f in self.fixtures}
        self.assertEqual(ids, {f"G{i:03d}" for i in range(1, 13)})


class TestConditionalValues(unittest.TestCase):
    """Verify the DB-important conditional facts resolve as intended (G012 + extras)."""
    @classmethod
    def setUpClass(cls):
        kb._init()

    def test_uny_rate_coop(self):
        fp = kb.FPS['FP-NSFDC-UNY-007']
        self.assertEqual(13, kb.resolve_conditional(fp['value'], {'channel_type': 'Co-operative Banks'}))
        self.assertEqual(13, kb.resolve_conditional(fp['value'], {'channel_type': 'Co-operative Societies'}))
        self.assertEqual(15, kb.resolve_conditional(fp['value'], {'channel_type': 'Small Finance Banks (SFBs)'}))

    def test_els_repayment(self):
        fp = kb.FPS['FP-NSFDC-ELS-008']
        self.assertEqual(12, kb.resolve_conditional(fp['value'], {'repayment_has_started': False}))
        self.assertEqual(10, kb.resolve_conditional(fp['value'], {'repayment_has_started': True}))

    def test_els_moratorium(self):
        fp = kb.FPS['FP-NSFDC-ELS-009']
        self.assertEqual('Course period + 1 year', kb.resolve_conditional(fp['value'], {'repayment_has_started': False}))
        self.assertEqual('up to 6 months', kb.resolve_conditional(fp['value'], {'repayment_has_started': True}))

    def test_tl_moratorium(self):
        fp = kb.FPS['FP-NSFDC-TL-009']
        self.assertEqual(12, kb.resolve_conditional(fp['value'], {'activity_category': 'Plantation'}))
        self.assertEqual(12, kb.resolve_conditional(fp['value'], {'activity_category': 'Construction'}))
        self.assertEqual(6, kb.resolve_conditional(fp['value'], {'activity_category': 'Bakery'}))

    def test_els_cap_formula(self):
        cap, _ = kb.els_cap({'course_fee': 3000000})
        self.assertEqual(2700000, cap)
        cap, _ = kb.els_cap({'course_fee': 6000000})
        self.assertEqual(4000000, cap)


if __name__ == '__main__':
    unittest.main()