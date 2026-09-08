"""Shared fixtures. Uses an in-memory SQLite database seeded with the prototype
data, and overrides the app's database dependency so no Postgres is needed."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  registers every table on Base.metadata
from app.db.base import Base
from app.db.seed_data import seed_prototype_data
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def seeded(session_factory):
    db = session_factory()
    try:
        seed_prototype_data(db)
    finally:
        db.close()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


BUSINESS_PROFILE = {
    "is_sc": True,
    "annual_income": 350000,
    "purpose": "business",
    "activity": "tailoring",
    "project_cost": 300000,
    "education_status": None,
    "course": None,
    "location": {"lat": 17.385, "lng": 78.4867},
}

EDUCATION_PROFILE = {
    "is_sc": True,
    "annual_income": 250000,
    "purpose": "education",
    "activity": None,
    "project_cost": 800000,
    "education_status": "admitted",
    "course": "B.Tech",
}

HYDERABAD = {"lat": 17.385, "lng": 78.4867}
