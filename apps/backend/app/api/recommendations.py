from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.intelligence.engine import RecommendationEngine, get_engine
from app.schemas.common import ErrorResponse
from app.schemas.recommendation import RecommendRequest, RecommendResponse
from app.services import recommendation_service

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "The recommendation engine could not be reached"},
    },
    summary="Ranked scheme recommendations",
    description=(
        "Sends the structured beneficiary profile to the intelligence engine and returns ranked "
        "schemes enriched with stored terms. Eligible schemes come first. When engine.is_prototype "
        "is true the reasons come from the placeholder engine and must be labelled as prototype output."
    ),
)
def recommend(
    req: RecommendRequest,
    db: Session = Depends(get_db),
    engine: RecommendationEngine = Depends(get_engine),
) -> RecommendResponse:
    return recommendation_service.recommend(db, req, engine)
