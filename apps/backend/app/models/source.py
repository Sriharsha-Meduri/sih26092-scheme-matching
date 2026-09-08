from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Source(Base):
    """Provenance registry. Every government fact points at one of these rows.

    source_type is one of: official, prototype_mock, derived. Prototype rows
    exist so the app can run before verified data arrives; they must always be
    labelled as such in any response."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    authority: Mapped[str | None] = mapped_column(String(200))
    published_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    verification_date: Mapped[date | None] = mapped_column(Date)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
