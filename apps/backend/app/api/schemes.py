from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.repositories import scheme_repository
from app.schemas.common import ErrorResponse, source_info
from app.schemas.scheme import SchemeDetail, SchemeSummary

router = APIRouter(prefix="/schemes", tags=["schemes"])


def _summary(scheme) -> SchemeSummary:
    data = SchemeSummary.model_validate(scheme, from_attributes=True)
    data.source = source_info(scheme.source)
    return data


@router.get(
    "",
    response_model=list[SchemeSummary],
    summary="List active schemes",
    description="Every active scheme with its key terms and provenance. Null numeric fields mean the value is not available from the current source.",
)
def list_schemes(db: Session = Depends(get_db)) -> list[SchemeSummary]:
    return [_summary(s) for s in scheme_repository.list_active(db)]


@router.get(
    "/{scheme_id}",
    response_model=SchemeDetail,
    responses={404: {"model": ErrorResponse, "description": "Scheme not found"}},
    summary="Get one scheme",
    description="Full scheme detail including its stored eligibility rules and application document requirements.",
)
def get_scheme(scheme_id: str, db: Session = Depends(get_db)) -> SchemeDetail:
    scheme = scheme_repository.get_by_scheme_id(db, scheme_id)
    if scheme is None:
        raise NotFoundError(f"Scheme {scheme_id} not found")
    detail = SchemeDetail.model_validate(scheme, from_attributes=True)
    detail.source = source_info(scheme.source)
    return detail
