from .models import Job


def create_job(db, job_data):
    new_job = Job(**job_data)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


def get_job(db, job_id):
    return db.get(Job, job_id)


def update_job(db, job_id, status, result=None, completed_at=None):
    job = get_job(db, job_id)
    if job is None:
        return None

    job.status = status
    job.result = result
    job.completed_at = completed_at
    db.commit()
    db.refresh(job)
    return job
