"""Result models (intelligence output contract).

Design goals (M2 §12, §17, §19):
- strongly typed dataclasses (pure Python),
- JSON-serializable via intelligence.utils.dataclass_to_dict,
- backend/frontend-friendly and stable,
- every element traceable: rule ids, reason keys, source ids, verification status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from intelligence.models.enums import (
    Factor,
    MatchStatus,
    OverallStatus,
    PartnerStatus,
    VerificationStatus,
    Verdict,
)


@dataclass
class SourceRef:
    source_id: str
    title: str = ""
    url: Optional[str] = None
    role: str = "REFERENCE"   # PRIMARY | CORROBORATING | CONFLICTING | REFERENCE


@dataclass
class RuleResult:
    """One eligibility-rule evaluation (M2 §8)."""

    rule_id: str
    name: str
    field: str
    operator: str
    expected_value: object
    actual_value: object
    result: Verdict
    reason_key: str
    scope_type: str
    scheme_ids: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    data_quality_issues: list[str] = field(default_factory=list)


@dataclass
class EligibilityResult:
    scheme_id: str
    verdict: Verdict
    rule_results: list[RuleResult] = field(default_factory=list)
    verification: Optional[VerificationStatus] = None
    # convenience: ids split by result for frontend drilling
    passed_rule_ids: list[str] = field(default_factory=list)
    failed_rule_ids: list[str] = field(default_factory=list)
    unknown_rule_ids: list[str] = field(default_factory=list)

    @property
    def applicable_rules(self) -> int:
        return len(self.rule_results)


@dataclass
class ActivityMatchResult:
    scheme_id: str
    status: MatchStatus
    reason_key: str
    raw_activity: Optional[str] = None
    canonical_activity_id: Optional[str] = None
    canonical_activity_name: Optional[str] = None
    sector_ids: list[str] = field(default_factory=list)
    verification: Optional[VerificationStatus] = None
    mapping_sources: list[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class FinancialConstraint:
    """One checked financial bound/formula term (M2 §10)."""

    parameter: str
    label: str
    expected: object
    actual: object
    passed: bool
    inclusivity: Optional[str] = None   # "inclusive" | "exclusive" | None
    source_ids: list[str] = field(default_factory=list)


@dataclass
class ConditionalResolution:
    """Resolved or unresolved conditional KB value (rates/repayment/moratorium)."""

    parameter: str
    variable: str
    resolved: bool
    value: object = None
    reason_key: str = ""
    note: str = ""


@dataclass
class FinancialFitResult:
    scheme_id: str
    status: Verdict
    project_cost: Optional[float] = None
    course_fee: Optional[float] = None
    requested_amount: Optional[float] = None
    eligible_amount: Optional[float] = None
    max_possible_amount: Optional[float] = None
    financing_percent: Optional[float] = None
    constraints: list[FinancialConstraint] = field(default_factory=list)
    conditionals: list[ConditionalResolution] = field(default_factory=list)
    formula_detail: Optional[str] = None
    reason_keys: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    data_quality_issues: list[str] = field(default_factory=list)


@dataclass
class EducationFitResult:
    scheme_id: str
    status: MatchStatus
    reason_key: str
    course: Optional[str] = None
    course_family: Optional[str] = None
    matched_family_id: Optional[str] = None
    matched_family_name: Optional[str] = None
    levels: list[str] = field(default_factory=list)
    coverage_status: Optional[str] = None
    verification: Optional[VerificationStatus] = None
    sources: list[str] = field(default_factory=list)


@dataclass
class PartnerFitResult:
    scheme_id: str
    status: Verdict                    # UNKNOWN when data unavailable
    partner_status: PartnerStatus
    score: int = 0
    reason_key: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class FactorScore:
    factor: Factor
    state: str                 # VERDICT summary: "PASS"/"FAIL"/"UNKNOWN"/"NOT_APPLICABLE"/"UNAVAILABLE"
    score: float               # 0..100
    weight: float
    detail: str = ""


@dataclass
class SchemeRecommendation:
    """One ranked candidate (M2 §12, §17)."""

    scheme_id: str
    scheme_name: str
    rank: int = 0
    score: float = 0.0
    factor_scores: list[FactorScore] = field(default_factory=list)
    eligibility: EligibilityResult = field(default_factory=EligibilityResult)
    activity_match: ActivityMatchResult = field(default_factory=ActivityMatchResult)
    financial_fit: FinancialFitResult = field(default_factory=FinancialFitResult)
    education_fit: EducationFitResult = field(default_factory=EducationFitResult)
    partner_fit: PartnerFitResult = field(default_factory=PartnerFitResult)
    reasons: list[str] = field(default_factory=list)          # reason keys (i18n)
    warnings: list[str] = field(default_factory=list)         # reason keys surfaced as warnings
    missing_fields: list[str] = field(default_factory=list)   # canonical user-input field names
    sources: list[SourceRef] = field(default_factory=list)
    verification_status: Optional[VerificationStatus] = None


@dataclass
class ExcludedScheme:
    scheme_id: str
    scheme_name: str
    reason_key: str
    eligibility_verdict: Optional[Verdict] = None


@dataclass
class MissingFieldEntry:
    field: str
    scheme_ids: list[str] = field(default_factory=list)
    reason_keys: list[str] = field(default_factory=list)


@dataclass
class RequestSummary:
    purpose: str
    is_sc: Optional[bool] = None
    community: Optional[str] = None
    annual_family_income: Optional[float] = None
    entity_type: Optional[str] = None
    activity: Optional[str] = None
    project_cost: Optional[float] = None
    requested_loan_amount: Optional[float] = None
    course: Optional[str] = None
    course_family: Optional[str] = None
    course_fee: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None


@dataclass
class EngineMetadata:
    engine_name: str = "SIH26092 Intelligence Engine"
    engine_version: str = "1.0.0"
    kb_version: Optional[str] = None
    kb_schema_version: Optional[str] = None
    kb_generated_on: Optional[str] = None
    deterministic: bool = True
    llm_used: bool = False


@dataclass
class RecommendationResponse:
    overall_status: OverallStatus
    recommendations: list[SchemeRecommendation] = field(default_factory=list)
    excluded_schemes: list[ExcludedScheme] = field(default_factory=list)
    missing_information: list[MissingFieldEntry] = field(default_factory=list)
    request_summary: RequestSummary = field(default_factory=RequestSummary)
    engine_metadata: EngineMetadata = field(default_factory=EngineMetadata)
    disclaimer: str = (
        "Informational guidance based on published scheme rules. "
        "Not an official government decision or loan approval."
    )