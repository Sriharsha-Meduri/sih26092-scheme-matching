from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scheme(Base):
    """Scheme financial and product parameters (PRD 10.1).

    Every money and rate column is nullable on purpose. A null means the value
    is not available from the current source; it is never a default."""

    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    scheme_type: Mapped[str | None] = mapped_column(String(60))
    purpose: Mapped[str | None] = mapped_column(String(40), index=True)  # business | education

    project_cost_min: Mapped[float | None] = mapped_column(Float)
    project_cost_max: Mapped[float | None] = mapped_column(Float)
    max_loan_amount: Mapped[float | None] = mapped_column(Float)
    financing_percentage: Mapped[float | None] = mapped_column(Float)
    nsfdc_interest_rate: Mapped[float | None] = mapped_column(Float)
    beneficiary_interest_rate: Mapped[float | None] = mapped_column(Float)
    repayment_period_months: Mapped[int | None] = mapped_column(Integer)
    moratorium_period_months: Mapped[int | None] = mapped_column(Integer)
    installment_frequency: Mapped[str | None] = mapped_column(String(40))

    target_group: Mapped[str | None] = mapped_column(String(200))
    application_mode: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)

    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    source = relationship("Source", lazy="joined")
    eligibility_rules = relationship(
        "EligibilityRule", back_populates="scheme", cascade="all, delete-orphan", order_by="EligibilityRule.priority"
    )
    application_requirements = relationship(
        "ApplicationRequirement", back_populates="scheme", cascade="all, delete-orphan"
    )
    partner_mappings = relationship("SchemePartnerMapping", back_populates="scheme", cascade="all, delete-orphan")


class EligibilityRule(Base):
    """Structured eligibility conditions stored as data (PRD 10.2).

    The backend stores and exposes these. Evaluating them is Developer 1's job."""

    __tablename__ = "eligibility_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(80), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(40))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    explanation: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)

    scheme = relationship("Scheme", back_populates="eligibility_rules")


class ApplicationRequirement(Base):
    """Scheme specific document requirements (PRD 10.7)."""

    __tablename__ = "application_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    document_name: Mapped[str] = mapped_column(String(200), nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))

    scheme = relationship("Scheme", back_populates="application_requirements")
