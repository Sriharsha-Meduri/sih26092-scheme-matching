"""Eligibility evaluation (M2 §8, §21-B/E)."""

import pytest

from intelligence.eligibility.evaluator import evaluate_scheme
from intelligence.kb.repository import KnowledgeBase
from intelligence.models.enums import VerificationStatus, Verdict

KB = KnowledgeBase()


def ctx(**overrides):
    base = {
        "community": "Scheduled Caste (SC)",
        "annual_family_income": 300000,
        "caste_certificate": True,
        "entity_type": "Individual",
    }
    base.update(overrides)
    return base


class TestRules:
    def test_all_pass(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx())
        assert res.verdict is Verdict.PASS
        assert res.verification is VerificationStatus.VERIFIED
        assert res.applicable_rules == 6  # E001-E006, E007 excluded (EXTERNAL_DOMAIN)

    def test_income_at_ceiling_inclusive(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(annual_family_income=500000))
        assert res.verdict is Verdict.PASS

    def test_income_above_ceiling_fails(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(annual_family_income=500001))
        assert res.verdict is Verdict.FAIL
        assert "E002" in res.failed_rule_ids

    def test_non_sc_fails(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(community="General (non-SC)"))
        assert res.verdict is Verdict.FAIL
        assert "E001" in res.failed_rule_ids

    def test_missing_certificate_fails(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(caste_certificate=False))
        assert res.verdict is Verdict.FAIL
        assert "E003" in res.failed_rule_ids

    def test_missing_income_unknown_not_fail(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(annual_family_income=None))
        assert res.verdict is Verdict.UNKNOWN
        assert "E002" in res.unknown_rule_ids
        assert res.verification is VerificationStatus.UNVERIFIED

    def test_entity_type_or_group(self):
        for entity in ("Individual", "Partnership Firm", "Co-operative Society"):
            res = evaluate_scheme(KB, "NSFDC-MFS", ctx(entity_type=entity))
            assert res.verdict is Verdict.PASS, entity

    def test_entity_type_not_allowed(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(entity_type="Private Limited Company"))
        assert res.verdict is Verdict.FAIL

    def test_missing_entity_unknown(self):
        res = evaluate_scheme(KB, "NSFDC-MFS", ctx(entity_type=None))
        assert res.verdict is Verdict.UNKNOWN

    def test_all_core_rules_apply_to_els(self):
        res = evaluate_scheme(KB, "NSFDC-ELS", ctx())
        assert res.verdict is Verdict.PASS
        assert "E001" in res.passed_rule_ids


class TestScopes:
    def test_external_domain_rule_not_applied(self):
        # E007 (EXTERNAL_DOMAIN) must never gate a loan scheme
        for sid in ("NSFDC-MFS", "NSFDC-TL", "NSFDC-ELS"):
            rule_ids = [r.rule_id for r in evaluate_scheme(KB, sid, ctx()).rule_results]
            assert "E007" not in rule_ids

    def test_scheme_group_income_rules_not_on_els(self):
        ids = [r.rule_id for r in evaluate_scheme(KB, "NSFDC-ELS", ctx()).rule_results]
        assert "E004" not in ids and "E005" not in ids and "E006" not in ids

    def test_scheme_list_via_group(self):
        # income_generating group covers the 4 non-education schemes
        for sid in ("NSFDC-MFS", "NSFDC-TL", "NSFDC-AMY", "NSFDC-UNY"):
            ids = [r.rule_id for r in evaluate_scheme(KB, sid, ctx()).rule_results]
            assert "E004" in ids