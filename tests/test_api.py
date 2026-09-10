import json
import os
import subprocess
import sys
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database, main, worker
from app.crud import create_job, get_job


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", factory)
    with TestClient(main.app) as client:
        yield client, factory


def test_job_lifecycle(client):
    client, factory = client
    response = client.post("/jobs")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "queued"
    assert job["result"] is None
    assert job["submitted_at"] is not None
    assert job["completed_at"] is None
    # TestClient waits for background tasks before returning the response.
    saved = client.get(f'/jobs/{job["id"]}').json()
    assert saved["status"] == "completed"
    assert saved["result"] == "Work completed"
    assert saved["completed_at"] >= saved["submitted_at"]
    result_url = f'/jobs/{job["id"]}/result'
    response = client.get(result_url)
    assert response.status_code == 200
    assert response.json() == {
        "job_id": job["id"], "status": "completed", "result": "Work completed",
        "completed_at": saved["completed_at"],
    }
    assert client.post("/jobs").json()["id"] != job["id"]


@pytest.mark.parametrize("status", ["queued", "processing"])
def test_pending_result(client, status):
    client, factory = client
    with factory() as db:
        job_id = create_job(db, {"status": status}).id
    response = client.get(f"/jobs/{job_id}/result")
    assert response.status_code == 200
    assert response.json() == {
        "job_id": job_id, "status": status, "result": None,
        "completed_at": None,
    }


@pytest.mark.parametrize("fails", [False, True])
def test_background_processing(client, monkeypatch, fails):
    client, factory = client
    observed = []

    def task():
        # A fresh reader must see the committed intermediate state.
        with factory() as db:
            from app.models import Job
            job = db.query(Job).one()
            observed.append(job.status)
            assert job.result is None
            assert job.completed_at is None
        if fails:
            raise RuntimeError("simulated failure")
        return "test result"

    monkeypatch.setattr(worker, "simulate_work", task)
    response = client.post("/jobs")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "queued"
    assert observed == ["processing"]
    with factory() as db:
        saved = get_job(db, job["id"])
        assert saved.status == ("failed" if fails else "completed")
        assert saved.result == (None if fails else "test result")
        assert saved.completed_at >= saved.submitted_at
    result = client.get(f'/jobs/{job["id"]}/result').json()
    assert result["status"] == ("failed" if fails else "completed")
    assert result["completed_at"] is not None


@pytest.mark.parametrize("path", ["/jobs/999", "/jobs/999/result"])
def test_missing_job(client, path):
    client, _ = client
    response = client.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


@pytest.mark.parametrize("fails", [False, True])
def test_session_closes(monkeypatch, fails):
    session = Mock()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    dependency = database.get_db()
    assert next(dependency) is session
    if fails:
        with pytest.raises(RuntimeError):
            dependency.throw(RuntimeError("request failed"))
    else:
        with pytest.raises(StopIteration):
            next(dependency)
    session.close.assert_called_once()


def test_job_survives_application_restart(tmp_path):
    # Set TEST_DATABASE_URL to run the same process-restart test on PostgreSQL.
    env = dict(os.environ, DATABASE_URL=os.getenv(
        "TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'jobs.db'}"
    ))
    def run(code):
        completed = subprocess.run(
            [sys.executable, "-c", code], env=env, check=True,
            capture_output=True, text=True, timeout=30,
        )
        return json.loads(completed.stdout)

    job = run('''
import json
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    response = client.post("/jobs")
    assert response.status_code == 200
    print(json.dumps(client.get(f'/jobs/{response.json()["id"]}').json()))
''')
    saved = run(f'''
import json
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    response = client.get("/jobs/{job['id']}")
    assert response.status_code == 200
    result = client.get("/jobs/{job['id']}/result")
    assert result.status_code == 200
    assert result.json()["result"] == "Work completed"
    assert result.json()["completed_at"] is not None
    assert client.post("/jobs").json()["id"] > {job['id']}
    print(json.dumps(response.json()))
''')
    assert saved == job
