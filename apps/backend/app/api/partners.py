from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import BadRequestError
from app.db.session import get_db
from app.schemas.common import ErrorResponse
from app.schemas.partner import PartnerDetail, PartnersNearbyResponse
from app.services import partner_service

router = APIRouter(prefix="/partners", tags=["partners"])


# Declared before /{partner_id} so "nearby" is never captured as an id.
@router.get(
    "/nearby",
    response_model=PartnersNearbyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Radius above the configured maximum"},
        404: {"model": ErrorResponse, "description": "Scheme not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    summary="Nearby compatible partners",
    description=(
        "Channel partners near a location, filtered for the selected scheme and ranked by the "
        "documented formula (compatibility 40, distance 25, verified performance 20, availability 15). "
        "Partners explicitly not authorised for the scheme are excluded. Missing performance data is "
        "reported as unavailable and never treated as a good signal."
    ),
)
def partners_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitude", examples=[17.385]),
    lng: float = Query(..., ge=-180, le=180, description="Longitude", examples=[78.4867]),
    scheme_id: str | None = Query(None, max_length=50, description="Filter and rank for this scheme"),
    radius_km: float | None = Query(None, gt=0, description="Search radius in km (default 50, max 500)"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PartnersNearbyResponse:
    settings = get_settings()
    radius = radius_km if radius_km is not None else settings.default_partner_radius_km
    if radius > settings.max_partner_radius_km:
        raise BadRequestError(f"radius_km cannot exceed {settings.max_partner_radius_km:.0f}")
    return partner_service.find_nearby(db, lat, lng, scheme_id, radius, limit)


@router.get(
    "/{partner_id}",
    response_model=PartnerDetail,
    responses={404: {"model": ErrorResponse, "description": "Partner not found"}},
    summary="Partner detail",
    description="One partner with every scheme mapping and its verified performance record, if any.",
)
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> PartnerDetail:
    return partner_service.get_partner_detail(db, partner_id)
