from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Partner, Scheme
from app.repositories import partner_repository, scheme_repository
from app.schemas.common import source_info
from app.schemas.partner import (
    UNAVAILABLE_PERFORMANCE,
    NearbyQuery,
    PartnerDetail,
    PartnerNearbyItem,
    PartnerSchemeLink,
    PartnersNearbyResponse,
    PerformanceInfo,
    SchemeCompatibility,
)
from app.services.geo import haversine_km

RANKING_METHOD = (
    "Weighted score: scheme compatibility 40, distance 25, verified performance 20, "
    "availability 15. Missing data scores zero and is reported as unavailable."
)

WEIGHTS = {"compatibility": 0.40, "distance": 0.25, "performance": 0.20, "availability": 0.15}


def performance_info(partner: Partner) -> PerformanceInfo:
    """Only a verified record counts. No record means unavailable, never good."""
    record = partner_repository.latest_performance(partner)
    if record is None:
        return UNAVAILABLE_PERFORMANCE
    return PerformanceInfo(
        available=True,
        period=record.period,
        sanctioned_amount=record.sanctioned_amount,
        disbursed_amount=record.disbursed_amount,
        utilization_percentage=record.utilization_percentage,
        npa_percentage=record.npa_percentage,
        overdue_amount=record.overdue_amount,
        status=record.status,
        as_of_date=record.as_of_date,
    )


def compatibility_for(partner: Partner, scheme: Scheme | None) -> SchemeCompatibility | None:
    if scheme is None:
        return None
    mapping = next((m for m in partner.scheme_mappings if m.scheme_id == scheme.id), None)
    status = mapping.authorization_status if mapping else "unknown"
    compatible = True if status == "authorized" else None
    if status == "not_authorized":
        compatible = False
    return SchemeCompatibility(
        scheme_id=scheme.scheme_id,
        authorization_status=status,
        compatible=compatible,
        geographic_scope=mapping.geographic_scope if mapping else None,
    )


def rank_score(
    compat: SchemeCompatibility | None,
    distance_km: float,
    radius_km: float,
    perf: PerformanceInfo,
    status: str,
    scheme_selected: bool,
) -> float:
    """The documented ranking. Every component is 0 to 1; unavailable data is 0."""
    if scheme_selected:
        compat_score = 1.0 if (compat and compat.compatible is True) else 0.0
    else:
        # With no scheme chosen, compatibility cannot be judged; treat as neutral full weight
        # so distance and status drive the order rather than penalising everyone equally.
        compat_score = 1.0
    distance_score = max(0.0, 1.0 - (distance_km / radius_km)) if radius_km > 0 else 0.0
    perf_score = 0.0
    if perf.available and perf.utilization_percentage is not None:
        perf_score = max(0.0, min(1.0, perf.utilization_percentage / 100.0))
    availability_score = 1.0 if status == "active" else 0.0
    total = (
        WEIGHTS["compatibility"] * compat_score
        + WEIGHTS["distance"] * distance_score
        + WEIGHTS["performance"] * perf_score
        + WEIGHTS["availability"] * availability_score
    )
    return round(total * 100.0, 1)


def find_nearby(
    db: Session,
    lat: float,
    lng: float,
    scheme_id: str | None,
    radius_km: float,
    limit: int,
) -> PartnersNearbyResponse:
    scheme: Scheme | None = None
    if scheme_id:
        scheme = scheme_repository.get_by_scheme_id(db, scheme_id)
        if scheme is None:
            raise NotFoundError(f"Scheme {scheme_id} not found")

    results: list[PartnerNearbyItem] = []
    for partner in partner_repository.list_routable(db):
        distance = haversine_km(lat, lng, partner.latitude, partner.longitude)
        if distance > radius_km:
            continue

        compat = compatibility_for(partner, scheme)
        if compat is not None and compat.compatible is False:
            continue  # explicitly not authorised for this scheme

        perf = performance_info(partner)
        score = rank_score(compat, distance, radius_km, perf, partner.status, scheme is not None)
        results.append(
            PartnerNearbyItem(
                partner_id=partner.partner_id,
                name=partner.name,
                partner_type=partner.partner_type,
                address=partner.address,
                state=partner.state,
                district=partner.district,
                latitude=partner.latitude,
                longitude=partner.longitude,
                phone=partner.phone,
                email=partner.email,
                website=partner.website,
                status=partner.status,
                distance_km=round(distance, 2),
                scheme_compatibility=compat,
                performance=perf,
                rank_score=score,
                source_type=partner.source.source_type if partner.source else None,
            )
        )

    results.sort(key=lambda r: (-r.rank_score, r.distance_km))
    results = results[:limit]
    return PartnersNearbyResponse(
        query=NearbyQuery(lat=lat, lng=lng, scheme_id=scheme_id, radius_km=radius_km, limit=limit),
        count=len(results),
        ranking_method=RANKING_METHOD,
        results=results,
    )


def get_partner_detail(db: Session, partner_id: str) -> PartnerDetail:
    partner = partner_repository.get_by_partner_id(db, partner_id)
    if partner is None:
        raise NotFoundError(f"Partner {partner_id} not found")
    schemes = [
        PartnerSchemeLink(
            scheme_id=m.scheme.scheme_id,
            scheme_name=m.scheme.name,
            authorization_status=m.authorization_status,
            geographic_scope=m.geographic_scope,
        )
        for m in partner.scheme_mappings
        if m.scheme is not None
    ]
    return PartnerDetail(
        partner_id=partner.partner_id,
        name=partner.name,
        partner_type=partner.partner_type,
        address=partner.address,
        state=partner.state,
        district=partner.district,
        latitude=partner.latitude,
        longitude=partner.longitude,
        phone=partner.phone,
        email=partner.email,
        website=partner.website,
        status=partner.status,
        schemes=schemes,
        performance=performance_info(partner),
        source=source_info(partner.source),
    )
