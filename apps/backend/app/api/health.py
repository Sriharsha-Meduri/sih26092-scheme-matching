from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.intelligence.engine import RecommendationEngine, get_engine

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Liveness, plus whether the database and the recommendation engine are reachable.",
)
def health(db: Session = Depends(get_db), engine: RecommendationEngine = Depends(get_engine)) -> dict:
    settings = get_settings()
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        database = "error"
    return {
        "status": "ok" if database == "ok" else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.env,
        "database": database,
        "recommendation_engine": {"name": engine.name, "is_prototype": engine.is_prototype},
    }
