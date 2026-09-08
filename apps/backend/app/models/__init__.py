"""Import every model so Base.metadata knows about all tables."""

from app.models.source import Source
from app.models.scheme import Scheme, EligibilityRule, ApplicationRequirement
from app.models.partner import Partner, SchemePartnerMapping, PartnerPerformance
from app.models.activity import Activity
from app.models.els_course import ElsCourse

__all__ = [
    "Source",
    "Scheme",
    "EligibilityRule",
    "ApplicationRequirement",
    "Partner",
    "SchemePartnerMapping",
    "PartnerPerformance",
    "Activity",
    "ElsCourse",
]
