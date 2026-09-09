"""SIH26092 Intelligence Engine — pure-Python deterministic decision layer.

Public entry point:

    from intelligence import RecommendationEngine, RecommendationRequest

Interface contract (M0_COMPONENT_CONTRACTS §2): the engine consumes a typed
request (profile + requirement + location) and returns a strongly-typed,
JSON-serializable RecommendationResponse. No web framework, no LLM.
"""

from intelligence.engine import RecommendationEngine
from intelligence.models.profile import ApplicantProfile
from intelligence.models.requirement import Location, Requirement, RecommendationRequest
from intelligence.models.result import RecommendationResponse
from intelligence.kb.repository import KnowledgeBase

__version__ = "1.0.0"

__all__ = [
    "RecommendationEngine",
    "RecommendationRequest",
    "ApplicantProfile",
    "Requirement",
    "Location",
    "RecommendationResponse",
    "KnowledgeBase",
    "__version__",
]