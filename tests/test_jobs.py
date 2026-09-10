from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.crud import create_job, get_job, update_job
from app.database import Base


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_create_and_get_job(db):
    job = create_job(db, {"status": "queued", "result": None})
    job_id = job.id
    assert job_id is not None
    assert job.submitted_at is not None
    assert job.completed_at is None

    db.expunge_all()
    with Session(db.bind) as reader:
        saved_job = get_job(reader, job_id)
        assert saved_job.status == "queued"
        assert saved_job.result is None


def test_update_job_persists_fields(db):
    job = create_job(db, {"status": "queued"})
    job_id = job.id
    completed_at = datetime(2026, 9, 10, 12, 0)

    updated = update_job(db, job_id, "completed", "finished", completed_at)
    assert updated.id == job_id
    db.expunge_all()
    with Session(db.bind) as reader:
        saved_job = get_job(reader, job_id)
        assert saved_job.status == "completed"
        assert saved_job.result == "finished"
        assert saved_job.completed_at == completed_at

    updated = update_job(db, job_id, "queued")
    assert updated.result is None
    assert updated.completed_at is None


def test_missing_job(db):
    assert get_job(db, 999) is None
    assert update_job(db, 999, "completed", "finished") is None
