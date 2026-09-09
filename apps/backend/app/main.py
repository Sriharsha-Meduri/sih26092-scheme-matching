import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers

DESCRIPTION = """
Backend for SIH26092: MoSJE AI Scheme Matching for Marginalized Entrepreneurs.

The backend is the orchestration and data access layer. It validates input,
serves verified scheme and partner data with provenance, estimates EMIs, ranks
nearby channel partners, and forwards beneficiary profiles to the intelligence
engine. It never decides eligibility itself.

Every scheme and partner carries a `source_type`. Prototype data is labelled
`prototype_mock` and must be shown as such.
"""

TAGS = [
    {"name": "health", "description": "Liveness and dependency status."},
    {"name": "schemes", "description": "Scheme master with provenance, rules and document requirements."},
    {"name": "recommendations", "description": "Ranked scheme recommendations via the intelligence engine."},
    {"name": "calculator", "description": "Scheme aware EMI estimates."},
    {"name": "partners", "description": "Channel partner search, ranking and detail."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=DESCRIPTION,
        openapi_tags=TAGS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(api_router)
    return app


app = create_app()
