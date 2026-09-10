import logging
import time
from datetime import datetime, timezone

from . import database
from .crud import update_job

logger = logging.getLogger(__name__)


def simulate_work():
    """A small stand-in for a real task; runs outside the request handler."""
    time.sleep(0.1)
    return "Work completed"


def completion_time():
    # Existing database timestamps are stored as naive UTC values.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def process_job(job_id: int):
    """Use a separate session because the submitting request has finished."""
    with database.SessionLocal() as db:
        try:
            if update_job(db, job_id, "processing") is None:
                return
            result = simulate_work()
            update_job(db, job_id, "completed", result, completion_time())
        except Exception:
            db.rollback()
            logger.exception("Job %s failed", job_id)
            update_job(db, job_id, "failed", completed_at=completion_time())
