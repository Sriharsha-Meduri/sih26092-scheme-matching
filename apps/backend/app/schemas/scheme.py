from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SourceInfo


class EligibilityRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field: str
    operator: str
    value: str
    unit: str | None = None
    priority: int
    explanation: str | None = None


class ApplicationRequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_name: str
    mandatory: bool
    description: str | None = None


class SchemeFinancials(BaseModel):
    """The subset of scheme terms that recommendations and the calculator surface."""

    max_loan_amount: float | None = None
    financing_percentage: float | None = None
    beneficiary_interest_rate: float | None = None
    repayment_period_months: int | None = None
    moratorium_period_months: int | None = None
    project_cost_min: float | None = None
    project_cost_max: float | None = None


class SchemeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scheme_id: str
    name: str
    scheme_type: str | None = None
    purpose: str | None = None
    target_group: str | None = None
    project_cost_min: float | None = None
    project_cost_max: float | None = None
    max_loan_amount: float | None = None
    financing_percentage: float | None = None
    nsfdc_interest_rate: float | None = None
    beneficiary_interest_rate: float | None = None
    repayment_period_months: int | None = None
    moratorium_period_months: int | None = None
    installment_frequency: str | None = None
    application_mode: str | None = None
    status: str
    effective_from: date | None = None
    effective_until: date | None = None
    source: SourceInfo | None = None


class SchemeDetail(SchemeSummary):
    eligibility_rules: list[EligibilityRuleOut] = []
    application_requirements: list[ApplicationRequirementOut] = []
