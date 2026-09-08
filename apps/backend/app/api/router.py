from fastapi import APIRouter

from app.api import calculator, partners, recommendations, schemes

api_router = APIRouter(prefix="/api")
api_router.include_router(schemes.router)
api_router.include_router(recommendations.router)
api_router.include_router(calculator.router)
api_router.include_router(partners.router)
