from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SourceInfo


class SchemeCompatibility(BaseModel):
    scheme_id: str
    authorization_status: str  # authorized | not_authorized | unknown
    compatible: bool | None = None  # True for authorized, None for unknown
    geographic_scope: str | None = None


class PerformanceInfo(BaseModel):
    """Verified performance metrics. available is False and every metric is
    None when no verified record exists. Never treat None as a good signal."""

    available: bool
    period: str | None = None
    sanctioned_amount: float | None = None
    disbursed_amount: float | None = None
    utilization_percentage: float | None = None
    npa_percentage: float | None = None
    overdue_amount: float | None = None
    status: str | None = None
    as_of_date: date | None = None


UNAVAILABLE_PERFORMANCE = PerformanceInfo(available=False)


class PartnerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    partner_id: str
    name: str
    partner_type: str
    address: str | None = None
    state: str | None = None
    district: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    status: str


class PartnerNearbyItem(PartnerBase):
    distance_km: float
    scheme_compatibility: SchemeCompatibility | None = None
    performance: PerformanceInfo
    rank_score: float
    source_type: str | None = None


class NearbyQuery(BaseModel):
    lat: float
    lng: float
    scheme_id: str | None = None
    radius_km: float
    limit: int


class PartnersNearbyResponse(BaseModel):
    query: NearbyQuery
    count: int
    ranking_method: str
    results: list[PartnerNearbyItem]


class PartnerSchemeLink(BaseModel):
    scheme_id: str
    scheme_name: str
    authorization_status: str
    geographic_scope: str | None = None


class PartnerDetail(PartnerBase):
    schemes: list[PartnerSchemeLink] = []
    performance: PerformanceInfo
    source: SourceInfo | None = None
