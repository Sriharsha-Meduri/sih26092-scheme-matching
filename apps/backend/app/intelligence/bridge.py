"""Bridge to Developer 1's intelligence engine (the top-level `intelligence` package).

The backend's module adapter expects a plain callable:

    recommend(profile: dict, schemes: list[dict]) -> {"recommendations": [...]}

Their engine is a class with its own request and response dataclasses, so this
module translates in both directions and nothing else in the backend needs to
know the difference. Enable it with:

    RECOMMENDATION_ENGINE=module
    RECOMMENDATION_ENGINE_MODULE=app.intelligence.bridge:recommend

Reasons are passed through as the engine's stable i18n reason keys (for example
INCOME_WITHIN_LIMIT). The engine deliberately emits no free text; Developer 3
localises the keys to English, Hindi and Telugu in the frontend.

The engine locates KB/normalized by walking up from its own package, so it
works from any working directory as long as `intelligence` is importable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT_ENV = "SIH26092_REPO_ROOT"


def _ensure_importable() -> None:
    """Make the top-level `intelligence` package importable.

    It lives at the repository root, not inside the backend. In Docker it is
    copied next to `app/`; locally we add the repo root to sys.path."""
    try:
        import intelligence  # noqa: F401

        return
    except ModuleNotFoundError:
        pass

    candidates: list[Path] = []
    env_root = os.environ.get(REPO_ROOT_ENV)
    if env_root:
        candidates.append(Path(env_root).expanduser().resolve())
    # apps/backend/app/intelligence/bridge.py -> parents[4] is the repo root
    candidates.append(Path(__file__).resolve().parents[4])

    for root in candidates:
        if (root / "intelligence" / "__init__.py").is_file():
            sys.path.insert(0, str(root))
            return
    raise RuntimeError(
        "The `intelligence` package was not found. Set SIH26092_REPO_ROOT to the repository "
        "root or add it to PYTHONPATH."
    )


_engine: Any = None


def _get_engine():
    global _engine
    if _engine is None:
        _ensure_importable()
        from intelligence.engine import RecommendationEngine

        _engine = RecommendationEngine()
    return _engine


def recommend(profile: dict, schemes: list[dict]) -> dict:  # noqa: ARG001  schemes unused: the engine has its own KB
    """Adapter entry point. `schemes` is the backend's scheme context; the engine
    reads its own knowledge base, so it is accepted for interface compatibility
    and ignored."""
    _ensure_importable()
    from intelligence.models.enums import Verdict
    from intelligence.models.profile import ApplicantProfile
    from intelligence.models.requirement import Location, Requirement

    applicant = ApplicantProfile(
        is_sc=profile.get("is_sc"),
        annual_family_income=profile.get("annual_income"),
        education_status=profile.get("education_status"),
        caste_certificate=profile.get("caste_certificate"),
        entity_type=profile.get("entity_type"),
    )
    requirement = Requirement(
        purpose=profile.get("purpose"),
        activity=profile.get("activity"),
        project_cost=profile.get("project_cost"),
        course=profile.get("course"),
    )
    location = None
    loc = profile.get("location") or {}
    if loc.get("lat") is not None and loc.get("lng") is not None:
        location = Location(latitude=float(loc["lat"]), longitude=float(loc["lng"]))

    response = _get_engine().evaluate(applicant, requirement, location)

    items: list[dict] = []
    for rec in response.recommendations:
        verdict = getattr(rec.eligibility, "verdict", None)
        items.append(
            {
                "scheme_id": rec.scheme_id,
                "scheme_name": rec.scheme_name,
                "eligible": verdict == Verdict.PASS,
                "score": float(rec.score or 0),
                "reasons": list(rec.reasons) + list(rec.warnings),
            }
        )
    for ex in response.excluded_schemes:
        items.append(
            {
                "scheme_id": ex.scheme_id,
                "scheme_name": ex.scheme_name,
                "eligible": False,
                "score": 0,
                "reasons": [ex.reason_key] if ex.reason_key else [],
            }
        )

    status = response.overall_status
    return {
        "recommendations": items,
        "overall_status": getattr(status, "value", status),
        "missing_information": [
            {"field": m.field, "reason_keys": list(m.reason_keys)} for m in response.missing_information
        ],
    }


def engine_metadata() -> dict:
    """Engine identity for diagnostics (name, version, KB version)."""
    _ensure_importable()
    from intelligence.models.result import EngineMetadata

    meta = EngineMetadata()
    return {
        "engine_name": meta.engine_name,
        "engine_version": meta.engine_version,
        "deterministic": meta.deterministic,
        "llm_used": meta.llm_used,
    }
