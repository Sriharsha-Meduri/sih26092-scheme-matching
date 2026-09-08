from pydantic import BaseModel, ConfigDict, Field


class CalculateEmiRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "loan_amount": 300000,
                "interest_rate": 8,
                "tenure_months": 60,
                "moratorium_months": 3,
                "scheme_id": "NSFDC-TL",
            }
        }
    )

    loan_amount: float = Field(gt=0, description="Principal in INR")
    interest_rate: float | None = Field(
        default=None,
        ge=0,
        description="Annual interest rate in percent. May be omitted only when scheme_id is given and the scheme has a stored rate.",
    )
    tenure_months: int = Field(gt=0, description="Repayment tenure in months, after any moratorium")
    moratorium_months: int = Field(default=0, ge=0, description="Months before instalments begin")
    scheme_id: str | None = Field(default=None, max_length=50)


class SchemeLimitInfo(BaseModel):
    scheme_id: str
    scheme_name: str
    max_loan_amount: float | None = None
    within_scheme_limit: bool | None = None
    interest_rate_source: str  # request | scheme


class CalculateEmiResponse(BaseModel):
    loan_amount: float
    interest_rate: float
    tenure_months: int
    moratorium_months: int
    monthly_emi: float
    total_interest: float
    total_repayment: float
    total_duration_months: int
    moratorium_interest: float
    principal_after_moratorium: float
    is_estimate: bool = True
    method: str
    scheme: SchemeLimitInfo | None = None
