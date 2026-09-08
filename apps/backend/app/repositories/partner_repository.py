from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Partner, PartnerPerformance, SchemePartnerMapping


def _with_relations(stmt):
    return stmt.options(
        selectinload(Partner.scheme_mappings).selectinload(SchemePartnerMapping.scheme),
        selectinload(Partner.performance_records),
    )


def list_routable(db: Session) -> list[Partner]:
    """Partners that can appear in a search: not inactive, and geocoded."""
    stmt = _with_relations(
        select(Partner).where(
            Partner.status != "inactive",
            Partner.latitude.is_not(None),
            Partner.longitude.is_not(None),
        )
    )
    return list(db.scalars(stmt).all())


def get_by_partner_id(db: Session, partner_id: str) -> Partner | None:
    stmt = _with_relations(select(Partner).where(Partner.partner_id == partner_id))
    return db.scalars(stmt).first()


def latest_performance(partner: Partner) -> PartnerPerformance | None:
    records = partner.performance_records or []
    if not records:
        return None
    return max(records, key=lambda r: (r.as_of_date or date.min, r.id))
