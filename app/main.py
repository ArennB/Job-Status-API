from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .crud import create_job, get_job
from .database import Base, engine, get_db
from .schemas import JobResponse, JobResultResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(lifespan=lifespan)
DatabaseSession = Annotated[Session, Depends(get_db)]


@app.get("/")
def home():
    return {"message": "API is running"}


@app.post("/jobs", response_model=JobResponse)
def submit(db: DatabaseSession):
    return create_job(db, {"status": "queued", "result": None})


def require_job(db: Session, job_id: int):
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs/{job_id}", response_model=JobResponse)
def status(job_id: int, db: DatabaseSession):
    return require_job(db, job_id)


@app.get("/jobs/{job_id}/result", response_model=JobResultResponse)
def result(job_id: int, db: DatabaseSession):
    """Pending jobs return HTTP 200 with their current status and a null result."""
    job = require_job(db, job_id)
    return {"job_id": job.id, "status": job.status, "result": job.result}
