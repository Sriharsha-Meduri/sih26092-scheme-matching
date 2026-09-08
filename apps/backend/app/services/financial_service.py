from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.repositories import scheme_repository
from app.schemas.calculator import CalculateEmiRequest, CalculateEmiResponse, SchemeLimitInfo

EMI_METHOD = (
    "Reducing balance EMI. Simple interest accrues during the moratorium and is added to the "
    "principal before instalments begin. Instalments then run for the full tenure, so total "
    "duration is moratorium plus tenure. Estimate only; lender schedules may differ."
)


@dataclass
class EmiBreakdown:
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


def calculate_emi(
    loan_amount: float,
    annual_interest_rate: float,
    tenure_months: int,
    moratorium_months: int = 0,
) -> EmiBreakdown:
    """Pure EMI estimate. Validates its own inputs so it is safe to call from
    anywhere, not only behind the Pydantic layer.

    Moratorium treatment: no instalments during the moratorium, simple interest
    accrues on the principal for those months and is capitalised, then the
    reducing balance EMI runs for tenure_months. Zero interest divides the
    principal evenly."""
    if loan_amount is None or loan_amount <= 0:
        raise BadRequestError("loan_amount must be greater than 0")
    if annual_interest_rate is None or annual_interest_rate < 0:
        raise BadRequestError("interest_rate must be 0 or greater")
    if tenure_months is None or int(tenure_months) != tenure_months or tenure_months <= 0:
        raise BadRequestError("tenure_months must be a whole number greater than 0")
    if moratorium_months is None or int(moratorium_months) != moratorium_months or moratorium_months < 0:
        raise BadRequestError("moratorium_months must be a whole number of 0 or more")

    monthly_rate = annual_interest_rate / 12.0 / 100.0
    moratorium_interest = loan_amount * monthly_rate * moratorium_months
    principal = loan_amount + moratorium_interest

    if monthly_rate == 0:
        emi = principal / tenure_months
    else:
        growth = (1 + monthly_rate) ** tenure_months
        emi = principal * monthly_rate * growth / (growth - 1)

    total_repayment = emi * tenure_months
    total_interest = total_repayment - loan_amount

    return EmiBreakdown(
        loan_amount=round(loan_amount, 2),
        interest_rate=round(annual_interest_rate, 4),
        tenure_months=int(tenure_months),
        moratorium_months=int(moratorium_months),
        monthly_emi=round(emi, 2),
        total_interest=round(total_interest, 2),
        total_repayment=round(total_repayment, 2),
        total_duration_months=int(tenure_months + moratorium_months),
        moratorium_interest=round(moratorium_interest, 2),
        principal_after_moratorium=round(principal, 2),
    )


def calculate_emi_for_request(db: Session, req: CalculateEmiRequest) -> CalculateEmiResponse:
    """Scheme aware wrapper: resolves the rate from the scheme when omitted and
    refuses amounts above the scheme's stored limit."""
    rate = req.interest_rate
    rate_source = "request"
    scheme_info: SchemeLimitInfo | None = None

    if req.scheme_id:
        scheme = scheme_repository.get_by_scheme_id(db, req.scheme_id)
        if scheme is None:
            raise NotFoundError(f"Scheme {req.scheme_id} not found")

        if rate is None:
            if scheme.beneficiary_interest_rate is None:
                raise BadRequestError(
                    "interest_rate is required because this scheme has no stored beneficiary interest rate"
                )
            rate = scheme.beneficiary_interest_rate
            rate_source = "scheme"

        within: bool | None = None
        if scheme.max_loan_amount is not None:
            within = req.loan_amount <= scheme.max_loan_amount
            if not within:
                raise BadRequestError(
                    f"loan_amount exceeds the scheme limit of {scheme.max_loan_amount:.0f}",
                    details={
                        "scheme_id": scheme.scheme_id,
                        "max_loan_amount": scheme.max_loan_amount,
                        "requested_loan_amount": req.loan_amount,
                    },
                )

        scheme_info = SchemeLimitInfo(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            max_loan_amount=scheme.max_loan_amount,
            within_scheme_limit=within,
            interest_rate_source=rate_source,
        )
    elif rate is None:
        raise BadRequestError("interest_rate is required when no scheme_id is given")

    breakdown = calculate_emi(req.loan_amount, rate, req.tenure_months, req.moratorium_months)
    return CalculateEmiResponse(**asdict(breakdown), is_estimate=True, method=EMI_METHOD, scheme=scheme_info)
