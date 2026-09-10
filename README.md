# Job Status API

## Run with Docker Compose

Start Docker Desktop, then run:

```sh
cp .env.example .env
# Edit .env and choose a POSTGRES_PASSWORD.
docker compose up --build -d --wait
```

Open http://localhost:8000/docs or `curl http://localhost:8000/`.
Compose starts PostgreSQL, waits for its health check, then starts the API.
The API connects to `db:5432` on the Compose network and creates tables at startup.
Required settings are `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.
Optional `API_PORT` and `POSTGRES_PORT` change the published host ports.
Credentials are passed as separate fields, so passwords need no URL encoding.

Use `docker compose logs api db` to inspect startup and `docker compose down`
to stop the services. PostgreSQL data persists in the `postgres_data` volume.
The PostgreSQL initialization variables only apply to a new volume; when using
an existing volume, supply its existing credentials and database name.

## Run Python locally

The app reads process environment variables; it does not load `.env` itself.
After copying and editing `.env.example` as above, export its values:

```sh
set -a
. ./.env
set +a
docker compose up -d --wait db
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Local Python uses `DB_HOST=localhost` and `DB_PORT=5432` by default. If you
change `POSTGRES_PORT`, set `DB_PORT` to the same value for local Python.
Alternatively export `DATABASE_URL` (with URL-encoded credentials), which
overrides all separate database settings for local Python. Compose always
sets the API's host to `db` and port to `5432` using the shared credentials.
Missing credentials fail at startup with a configuration error.

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

Each API and CRUD test uses a fresh in-memory SQLite database, with request and
background worker sessions redirected to it and connections cleaned up after
the test. No running database server is needed. The suite covers generated job
IDs, initial status, retrieval, missing jobs, pending results, and successful and
failed background processing. A restart test uses a temporary SQLite file to
create a job in one Python process and retrieve it in a new process.
To verify that same restart behavior
against the local PostgreSQL database:

```sh
TEST_DATABASE_URL=postgresql://postgres:YOUR_URL_ENCODED_PASSWORD@localhost:5432/job_status_db \
  python -m pytest tests/test_api.py::test_job_survives_application_restart -q
```

The PostgreSQL test leaves two completed test jobs in the database.
