from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict


class SourceInfo(BaseModel):
    """Provenance attached to every scheme and partner response."""

    model_config = ConfigDict(from_attributes=True)

    source_type: str
    title: str | None = None
    url: str | None = None
    authority: str | None = None
    verification_date: date | None = None
    version: str | None = None
    notes: str | None = None


def source_info(src: Any) -> SourceInfo | None:
    if src is None:
        return None
    return SourceInfo.model_validate(src)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
