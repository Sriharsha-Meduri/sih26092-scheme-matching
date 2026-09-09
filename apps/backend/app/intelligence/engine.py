"""The recommendation engine boundary.

Developer 1 owns the real engine. The backend talks to it only through the
RecommendationEngine protocol below, and picks an implementation from
settings.recommendation_engine:

  mock    the backend's own placeholder for development (default)
  module  an importable Python callable, RECOMMENDATION_ENGINE_MODULE="pkg.mod:func"
          called as func(profile_dict, schemes_context_list) -> {"recommendations": [...]}
  http    a service, RECOMMENDATION_ENGINE_URL="http://engine/recommend"
          receives the profile dict as the JSON body and returns {"recommendations": [...]}

Output contract for every implementation (matches docs/API_CONTRACT.md):
  {"recommendations": [{"scheme_id", "scheme_name", "eligible", "score", "reasons"}]}
"""

import importlib
import logging
from typing import Any, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.errors import UpstreamError

log = logging.getLogger(__name__)


class BeneficiaryProfile(BaseModel):
    is_sc: bool
    annual_income: float
    purpose: str
    activity: str | None = None
    project_cost: float | None = None
    education_status: str | None = None
    course: str | None = None
    caste_certificate: bool | None = None
    entity_type: str | None = None
    location: dict[str, float] | None = None


class SchemeContext(BaseModel):
    """The scheme fields an in-process engine may want. Read-only context."""

    scheme_id: str
    name: str
    purpose: str | None = None
    project_cost_min: float | None = None
    project_cost_max: float | None = None
    max_loan_amount: float | None = None
    financing_percentage: float | None = None
    beneficiary_interest_rate: float | None = None
    repayment_period_months: int | None = None
    moratorium_period_months: int | None = None
    target_group: str | None = None

    @classmethod
    def from_scheme(cls, s: Any) -> "SchemeContext":
        return cls(
            scheme_id=s.scheme_id,
            name=s.name,
            purpose=s.purpose,
            project_cost_min=s.project_cost_min,
            project_cost_max=s.project_cost_max,
            max_loan_amount=s.max_loan_amount,
            financing_percentage=s.financing_percentage,
            beneficiary_interest_rate=s.beneficiary_interest_rate,
            repayment_period_months=s.repayment_period_months,
            moratorium_period_months=s.moratorium_period_months,
            target_group=s.target_group,
        )


class EngineRecommendation(BaseModel):
    scheme_id: str
    scheme_name: str | None = None
    eligible: bool
    score: float = 0
    reasons: list[str] = Field(default_factory=list)


class EngineResult(BaseModel):
    recommendations: list[EngineRecommendation]
    # Optional extras a real engine may report; the mock leaves them empty.
    overall_status: str | None = None
    missing_information: list[dict[str, Any]] = Field(default_factory=list)


@runtime_checkable
class RecommendationEngine(Protocol):
    name: str
    is_prototype: bool

    def recommend(self, profile: BeneficiaryProfile, schemes: list[SchemeContext]) -> EngineResult: ...


def _parse(raw: Any) -> EngineResult:
    try:
        return EngineResult.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise UpstreamError(f"Recommendation engine returned an unexpected shape: {exc}") from exc


class MockRecommendationEngine:
    """Development placeholder. Clearly labelled as prototype output.

    It uses only fields already stored on the scheme rows (purpose and the
    stored project cost range). It contains no government eligibility rules of
    its own, so it cannot drift into Developer 1's territory. Every reason
    string starts with "Prototype engine" so the UI can label it."""

    name = "mock"
    is_prototype = True

    def recommend(self, profile: BeneficiaryProfile, schemes: list[SchemeContext]) -> EngineResult:
        recs: list[EngineRecommendation] = []
        for s in schemes:
            reasons: list[str] = []
            eligible = True
            score = 0

            if s.purpose and s.purpose == profile.purpose:
                score += 60
                reasons.append(f"Prototype engine: scheme purpose ({s.purpose}) matches your stated purpose")
            else:
                eligible = False
                reasons.append(
                    f"Prototype engine: scheme purpose ({s.purpose or 'unspecified'}) does not match "
                    f"your stated purpose ({profile.purpose})"
                )

            if eligible and profile.project_cost is not None:
                if s.project_cost_max is not None and profile.project_cost > s.project_cost_max:
                    eligible = False
                    reasons.append(
                        f"Prototype engine: project cost {profile.project_cost:.0f} exceeds the scheme's "
                        f"stored project cost limit of {s.project_cost_max:.0f}"
                    )
                elif s.project_cost_min is not None and profile.project_cost < s.project_cost_min:
                    eligible = False
                    reasons.append(
                        f"Prototype engine: project cost {profile.project_cost:.0f} is below the scheme's "
                        f"stored minimum of {s.project_cost_min:.0f}"
                    )
                elif s.project_cost_max is not None or s.project_cost_min is not None:
                    score += 20
                    reasons.append("Prototype engine: project cost is within the scheme's stored project cost range")

            if eligible:
                if profile.purpose == "business" and profile.activity:
                    score += 10
                    reasons.append(
                        f"Prototype engine: activity '{profile.activity}' was provided "
                        "(activity eligibility is decided by the verified rule engine)"
                    )
                if profile.purpose == "education" and profile.course:
                    score += 10
                    reasons.append(
                        f"Prototype engine: course '{profile.course}' was provided "
                        "(course eligibility is decided by the verified rule engine)"
                    )
                score += 10
                reasons.append(
                    "Prototype engine: income was provided (income limits are decided by the verified rule engine)"
                )

            recs.append(
                EngineRecommendation(
                    scheme_id=s.scheme_id,
                    scheme_name=s.name,
                    eligible=eligible,
                    score=min(100, score) if eligible else 0,
                    reasons=reasons,
                )
            )
        return EngineResult(recommendations=recs)


class ModuleRecommendationEngine:
    """Adapter for an in-process engine: RECOMMENDATION_ENGINE_MODULE="pkg.mod:func"."""

    is_prototype = False

    def __init__(self, path: str):
        module_name, _, attr = path.partition(":")
        if not module_name or not attr:
            raise ValueError("RECOMMENDATION_ENGINE_MODULE must look like 'package.module:callable'")
        self._fn = getattr(importlib.import_module(module_name), attr)
        self.name = f"module:{path}"

    def recommend(self, profile: BeneficiaryProfile, schemes: list[SchemeContext]) -> EngineResult:
        try:
            raw = self._fn(profile.model_dump(), [s.model_dump() for s in schemes])
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError(f"Recommendation engine failed: {exc}") from exc
        return _parse(raw)


class HttpRecommendationEngine:
    """Adapter for an engine running as its own service."""

    is_prototype = False

    def __init__(self, url: str, timeout_seconds: float):
        self.url = url
        self.timeout = timeout_seconds
        self.name = f"http:{url}"

    def recommend(self, profile: BeneficiaryProfile, schemes: list[SchemeContext]) -> EngineResult:
        try:
            response = httpx.post(self.url, json=profile.model_dump(), timeout=self.timeout)
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPError as exc:
            raise UpstreamError(f"Recommendation engine request failed: {exc}") from exc
        return _parse(raw)


def build_engine(settings: Settings) -> RecommendationEngine:
    kind = (settings.recommendation_engine or "mock").lower()
    if kind == "module" and settings.recommendation_engine_module:
        return ModuleRecommendationEngine(settings.recommendation_engine_module)
    if kind == "http" and settings.recommendation_engine_url:
        return HttpRecommendationEngine(settings.recommendation_engine_url, settings.recommendation_engine_timeout_seconds)
    if kind != "mock":
        log.warning("RECOMMENDATION_ENGINE=%s is not fully configured, falling back to the mock engine", kind)
    return MockRecommendationEngine()


_engine: RecommendationEngine | None = None


def get_engine() -> RecommendationEngine:
    """FastAPI dependency. Built once per process; tests override it."""
    global _engine
    if _engine is None:
        _engine = build_engine(get_settings())
    return _engine
