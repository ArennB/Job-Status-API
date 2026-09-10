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

- `POST /jobs` creates a queued job with a database-generated ID. No request body
  is accepted yet, so no input schema is needed.
- `GET /jobs/{job_id}` returns `id`, `status`, and `result`.
- `GET /jobs/{job_id}/result` returns `job_id`, `status`, and `result`. Pending
  jobs return HTTP 200 with their current status and `result: null`.
- Both GET endpoints return HTTP 404 with `{"detail": "Job not found"}` for
  a missing job.

Jobs remain queued until a worker or other code updates them; this API does not
execute jobs yet. Each request closes its database session when it finishes.

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

The PostgreSQL test leaves two queued test jobs in the database.
