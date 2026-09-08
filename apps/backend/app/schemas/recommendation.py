from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.scheme import SchemeFinancials


class Purpose(str, Enum):
    business = "business"
    education = "education"


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90, description="Latitude in decimal degrees")
    lng: float = Field(ge=-180, le=180, description="Longitude in decimal degrees")


class RecommendRequest(BaseModel):
    """The structured beneficiary profile. The AI layer produces this from
    natural language; the backend only validates it and forwards it."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_sc": True,
                "annual_income": 350000,
                "purpose": "business",
                "activity": "tailoring",
                "project_cost": 300000,
                "education_status": None,
                "course": None,
                "location": {"lat": 17.385, "lng": 78.4867},
            }
        }
    )

    is_sc: bool = Field(description="Whether the applicant belongs to a Scheduled Caste")
    annual_income: float = Field(ge=0, description="Annual family income in INR")
    purpose: Purpose
    activity: str | None = Field(default=None, max_length=200)
    project_cost: float | None = Field(default=None, ge=0, description="Total project cost in INR")
    education_status: str | None = Field(default=None, max_length=200)
    course: str | None = Field(default=None, max_length=200)
    location: Location | None = None


class EngineInfo(BaseModel):
    name: str
    is_prototype: bool


class RecommendationItem(BaseModel):
    scheme_id: str
    scheme_name: str
    eligible: bool
    score: int = Field(ge=0, le=100, description="Internal ranking score, not a probability")
    reasons: list[str]
    scheme: SchemeFinancials | None = None
    source_type: str | None = None


class RecommendResponse(BaseModel):
    recommendations: list[RecommendationItem]
    engine: EngineInfo
    disclaimer: str
