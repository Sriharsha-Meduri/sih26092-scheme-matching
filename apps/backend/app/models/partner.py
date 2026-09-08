from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Partner(Base):
    """Authorised channel partner master (PRD 10.4).

    partner_type: SCA | PSB | RRB | NBFC_MFI | OTHER
    status: active | inactive | unknown"""

    __tablename__ = "partners"
    __table_args__ = (Index("ix_partners_lat_lng", "latitude", "longitude"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    partner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(200))
    website: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown", index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    source = relationship("Source", lazy="joined")
    scheme_mappings = relationship("SchemePartnerMapping", back_populates="partner", cascade="all, delete-orphan")
    performance_records = relationship(
        "PartnerPerformance", back_populates="partner", cascade="all, delete-orphan"
    )


class SchemePartnerMapping(Base):
    """Which partner may process which scheme (PRD 10.5).

    authorization_status: authorized | not_authorized | unknown.
    Missing rows mean unknown, never authorised."""

    __tablename__ = "scheme_partner_mapping"
    __table_args__ = (UniqueConstraint("scheme_id", "partner_id", name="uq_scheme_partner"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    authorization_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    geographic_scope: Mapped[str | None] = mapped_column(String(200))
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))

    scheme = relationship("Scheme", back_populates="partner_mappings")
    partner = relationship("Partner", back_populates="scheme_mappings")


class PartnerPerformance(Base):
    """Official partner performance and availability metrics (PRD 10.6).

    Only ever populated from a verified source. Every metric is nullable. The
    absence of a row means the metric is unavailable and the API says so."""

    __tablename__ = "partner_performance"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    period: Mapped[str | None] = mapped_column(String(50))
    sanctioned_amount: Mapped[float | None] = mapped_column(Float)
    disbursed_amount: Mapped[float | None] = mapped_column(Float)
    utilization_percentage: Mapped[float | None] = mapped_column(Float)
    beneficiary_count: Mapped[int | None] = mapped_column(Integer)
    pending_amount: Mapped[float | None] = mapped_column(Float)
    npa_percentage: Mapped[float | None] = mapped_column(Float)
    overdue_amount: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(String(40))
    as_of_date: Mapped[date | None] = mapped_column(Date)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))

    partner = relationship("Partner", back_populates="performance_records")
