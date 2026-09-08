from sqlalchemy.orm import Session

from app.intelligence.engine import BeneficiaryProfile, RecommendationEngine, SchemeContext
from app.repositories import scheme_repository
from app.schemas.recommendation import EngineInfo, RecommendationItem, RecommendRequest, RecommendResponse
from app.schemas.scheme import SchemeFinancials

DISCLAIMER = (
    "Based on the configured eligibility rules and available scheme information, these "
    "schemes appear to match your profile. This is guidance, not a government approval."
)


def recommend(db: Session, req: RecommendRequest, engine: RecommendationEngine) -> RecommendResponse:
    """Orchestrates one recommendation: builds the profile, asks the engine,
    then enriches the answer with scheme terms from the database. The backend
    never decides eligibility itself."""
    schemes = scheme_repository.list_active(db)
    by_id = {s.scheme_id: s for s in schemes}

    profile = BeneficiaryProfile(
        is_sc=req.is_sc,
        annual_income=req.annual_income,
        purpose=req.purpose.value,
        activity=req.activity,
        project_cost=req.project_cost,
        education_status=req.education_status,
        course=req.course,
        location=req.location.model_dump() if req.location else None,
    )
    context = [SchemeContext.from_scheme(s) for s in schemes]

    result = engine.recommend(profile, context)

    items: list[RecommendationItem] = []
    for rec in result.recommendations:
        scheme = by_id.get(rec.scheme_id)
        items.append(
            RecommendationItem(
                scheme_id=rec.scheme_id,
                scheme_name=rec.scheme_name or (scheme.name if scheme else rec.scheme_id),
                eligible=rec.eligible,
                score=max(0, min(100, int(round(rec.score)))),
                reasons=list(rec.reasons),
                scheme=SchemeFinancials.model_validate(scheme, from_attributes=True) if scheme else None,
                source_type=(scheme.source.source_type if scheme and scheme.source else None),
            )
        )

    items.sort(key=lambda i: (not i.eligible, -i.score, i.scheme_id))
    return RecommendResponse(
        recommendations=items,
        engine=EngineInfo(name=engine.name, is_prototype=engine.is_prototype),
        disclaimer=DISCLAIMER,
    )
