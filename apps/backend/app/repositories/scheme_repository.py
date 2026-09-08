from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Scheme


def list_active(db: Session) -> list[Scheme]:
    stmt = select(Scheme).where(Scheme.status == "active").order_by(Scheme.scheme_id)
    return list(db.scalars(stmt).all())


def get_by_scheme_id(db: Session, scheme_id: str) -> Scheme | None:
    stmt = (
        select(Scheme)
        .where(Scheme.scheme_id == scheme_id)
        .options(selectinload(Scheme.eligibility_rules), selectinload(Scheme.application_requirements))
    )
    return db.scalars(stmt).first()
