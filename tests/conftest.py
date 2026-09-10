import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Tests supply their own database configuration before importing the app.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from app import database, main


@pytest.fixture
def session_factory():
    """Give each test a fresh database shared by request and worker threads."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    database.Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()


@pytest.fixture
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture
def client(monkeypatch, session_factory):
    # Redirect startup, request sessions, and background worker sessions so no
    # part of the application connects to the configured application database.
    monkeypatch.setattr(main, "engine", session_factory.kw["bind"])
    monkeypatch.setattr(database, "SessionLocal", session_factory)
    with TestClient(main.app) as test_client:
        yield test_client, session_factory
