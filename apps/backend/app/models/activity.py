from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Activity(Base):
    """Government listed activity taxonomy (PRD 10.3). Owned by Developer 1."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    sub_sector: Mapped[str | None] = mapped_column(String(100))
    keywords: Mapped[list | None] = mapped_column(JSON)
    aliases: Mapped[list | None] = mapped_column(JSON)
