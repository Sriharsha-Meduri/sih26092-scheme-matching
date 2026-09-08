from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.calculator import CalculateEmiRequest, CalculateEmiResponse
from app.schemas.common import ErrorResponse
from app.services import financial_service

router = APIRouter(tags=["calculator"])


@router.post(
    "/calculate-emi",
    response_model=CalculateEmiResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Loan above scheme limit, or a missing rate"},
        404: {"model": ErrorResponse, "description": "Scheme not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    summary="Estimate EMI",
    description=(
        "An estimated repayment summary, not an official lender schedule. Reducing balance EMI; "
        "simple interest accrues during the moratorium and is added to the principal before "
        "instalments begin. If scheme_id is given, the amount is checked against the scheme limit "
        "and the stored beneficiary rate is used when interest_rate is omitted."
    ),
)
def calculate_emi(req: CalculateEmiRequest, db: Session = Depends(get_db)) -> CalculateEmiResponse:
    return financial_service.calculate_emi_for_request(db, req)
