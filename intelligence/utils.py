"""Small serialization helpers for the Intelligence Engine result models.

The engine deliberately has no pydantic dependency (pure Python, M2 directive).
These helpers give dataclass models JSON-safe dict() serialization so FastAPI /
frontend can consume them directly.
"""

from __future__ import annotations

import dataclasses
from datetime import date
from enum import Enum
from typing import Any


def dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """Recursively convert a dataclass (with enum/date/list/dict fields) to plain JSON-safe data."""
    return _convert(obj)


def _convert(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_convert(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _convert(v) for k, v in value.items()}
    if dataclasses.is_dataclass(value):
        return {
            f.name: _convert(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    return str(value)