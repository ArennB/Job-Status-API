# Job Status API

## Run locally

Start Docker Desktop, then run:

```sh
docker compose up -d db
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API defaults to the PostgreSQL connection in `.env.example`. To use another
instance, export `DATABASE_URL` before starting the app. The app does not load
`.env` files automatically. Tables are created during application startup.
Docker Compose stores PostgreSQL data in the `postgres_data` volume.

## Jobs

- `POST /jobs` creates a queued job with a database-generated ID and schedules
  a short simulated task. No request body is needed.
- `GET /jobs/{job_id}` returns `id`, `status`, `result`, `submitted_at`, and
  `completed_at`.
- `GET /jobs/{job_id}/result` returns `job_id`, `status`, `result`, and
  `completed_at`. Pending
  jobs return HTTP 200 with their current status and `result: null`.
- Both GET endpoints return HTTP 404 with `{"detail": "Job not found"}` for
  a missing job.

After submission, a FastAPI background task saves `processing`, simulates work
for 0.1 seconds, then saves `completed` with the result `"Work completed"` and a
completion timestamp. Task errors are logged and save `failed` with a null result
and a completion timestamp. Timestamps are stored and returned as naive UTC.
Each request and background task uses its own database session.

Try `curl -X POST http://127.0.0.1:8000/jobs`, then poll
`curl http://127.0.0.1:8000/jobs/1` using the returned ID. The POST response shows
`queued`; the short `processing` state may finish between polls.

Background execution runs in the API process. Saved results survive restarts,
but interrupted queued or processing jobs are not automatically resumed.

## Tests

```sh
python -m pytest -q
```

Tests use SQLite by default, including a test that creates a job in one Python
process and retrieves it in a new process. To verify that same restart behavior
against the local PostgreSQL database:

```sh
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/job_status_db \
  python -m pytest tests/test_api.py::test_job_survives_application_restart -q
```

The PostgreSQL test leaves two completed test jobs in the database.
