"""Shared enums and constants for the Intelligence Engine.

All values are stable strings so results serialize cleanly and the frontend /
backend can localize them. Representing states as enums (rather than booleans
or ad-hoc strings) keeps the decision pipeline explicit.
"""

from __future__ import annotations

from enum import Enum


class Verdict(str, Enum):
    """Outcome of a single evaluation (rule, bound, match, fit).

    UNKNOWN must never be treated as FAIL: it means "cannot decide with the
    information provided" and drives the gap detector instead of a rejection.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MatchStatus(str, Enum):
    """Resolution of a taxonomic match (activity or course family)."""

    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class VerificationStatus(str, Enum):
    """Whether the facts backing a result are verified in the KB.

    UNVERIFIED means the KB flags the underlying fact as derived/assumed and
    awaiting human confirmation (e.g. the 146 activity->scheme mappings,
    DQ-012). It is surfaced, never silently promoted.
    """

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class AvailabilityFactor(str, Enum):
    PARTNER = "PARTNER"
    DATA = "DATA"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class PartnerStatus(str, Enum):
    """State of the partner-availability dimension.

    Only UNAVAILABLE exists today: M1 partner master is NOT_INGESTED
    (partners.json stub). Real data would introduce AVAILABLE later.
    """

    UNAVAILABLE = "UNAVAILABLE"


class OverallStatus(str, Enum):
    """Top-level decision state of a recommendation response."""

    MATCHED = "MATCHED"
    NO_MATCH = "NO_MATCH"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    UNSUPPORTED_ACTIVITY = "UNSUPPORTED_ACTIVITY"


class Purpose(str, Enum):
    """Kind of financing request. Drives deterministic candidate discovery."""

    BUSINESS = "business"
    EDUCATION = "education"
    UNKNOWN = "unknown"


class Factor(str, Enum):
    """Scoring dimensions with their frozen weights (M0 D3, PRD §7.2)."""

    ELIGIBILITY = "eligibility"
    ACTIVITY = "activity"
    FINANCIAL = "financial"
    PARTNER_AVAILABILITY = "partner_availability"

    @property
    def weight(self) -> float:
        return WEIGHTS[self]


WEIGHTS: dict[Factor, float] = {
    Factor.ELIGIBILITY: 0.40,
    Factor.ACTIVITY: 0.25,
    Factor.FINANCIAL: 0.20,
    Factor.PARTNER_AVAILABILITY: 0.15,
}

# Deterministic scheme priority for tie-breaking (KB schemes.json file order).
SCHEME_PRIORITY: tuple[str, ...] = (
    "NSFDC-MFS",
    "NSFDC-TL",
    "NSFDC-AMY",
    "NSFDC-UNY",
    "NSFDC-ELS",
)

INCOME_GENERATING_SCHEMES: tuple[str, ...] = (
    "NSFDC-MFS",
    "NSFDC-TL",
    "NSFDC-AMY",
    "NSFDC-UNY",
)

ALL_CORE_SCHEMES: tuple[str, ...] = INCOME_GENERATING_SCHEMES + ("NSFDC-ELS",)

INCOME_GROUP_NAME = "income_generating"

SC_COMMUNITY = "Scheduled Caste (SC)"

# Percentage points the score drops when an activity mapping is UNVERIFIED (DQ-012).
UNVERIFIED_ACTIVITY_SCORE = 80
VERIFIED_ACTIVITY_SCORE = 100
NO_MATCH_SCORE = 0
UNKNOWN_FACTOR_SCORE = 50