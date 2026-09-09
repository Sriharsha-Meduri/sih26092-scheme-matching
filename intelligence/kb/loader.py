"""KB filesystem loader.

Locates the M1 normalized KB deterministically and loads every entity file with
light structural integrity checks. The KB is the source of truth; the engine
never constructs its own copy of government facts (M2 hard constraint).

Resolution order:
  1. SIH26092_KB_DIR environment variable (absolute path to KB/normalized).
  2. Walk parent directories of this package until KB/normalized/index.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

KB_ENV = "SIH26092_KB_DIR"

ENTITY_FILES: dict[str, str] = {
    "index": "index.json",
    "schemes": "schemes.json",
    "eligibility_rules": "eligibility_rules.json",
    "financial_parameters": "financial_parameters.json",
    "sectors": "sectors.json",
    "activities": "activities.json",
    "activity_scheme_mappings": "activity_scheme_mappings.json",
    "education": "education.json",
    "document_requirements": "document_requirements.json",
    "sources": "sources.json",
    "provenance": "provenance.json",
    "partners": "partners.json",
    "data_quality_issues": "data_quality_issues.json",
    "golden_fixtures": "golden_fixtures.json",
}


class KBError(Exception):
    """Base KB-layer error."""


class KBIntegrityError(KBError):
    """Raised when the normalized KB is missing or structurally invalid."""


def find_kb_dir(start: Path | None = None) -> Path | None:
    env = os.environ.get(KB_ENV)
    if env:
        p = Path(env).expanduser().resolve()
        return p if (p / "index.json").is_file() else None
    start = (start or Path(__file__).resolve().parent).resolve()
    for cand in (start, *start.parents):
        if (cand / "KB" / "normalized" / "index.json").is_file():
            return cand / "KB" / "normalized"
    return None


def _read_json(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - defensive
        raise KBIntegrityError(f"cannot read {path.name}: {exc}") from exc


def load_normalized(kb_dir: Path) -> dict[str, Any]:
    """Load every entity file into a flat dict keyed by entity name."""
    data: dict[str, Any] = {}
    for name, rel in ENTITY_FILES.items():
        path = kb_dir / rel
        if not path.is_file():
            raise KBIntegrityError(f"missing normalized KB entity file: {rel}")
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise KBIntegrityError(f"entity file {rel} must be a JSON object")
        data[name] = payload

    # Structural sanity: records lists exist where expected.
    for entity_key in ("schemes", "eligibility_rules", "financial_parameters",
                       "activities", "sources"):
        records = data[entity_key].get("records")
        if not isinstance(records, list):
            raise KBIntegrityError(f"{entity_key}.records must be a list")
    activities = data["activities"]["records"]
    if not {
        "id", "name", "source_name", "sector_ids", "aliases", "sources"
    }.issubset(activities[0].keys()):
        raise KBIntegrityError(f"activities[0] missing canonical fields: {activities[0].keys()}")
    return data