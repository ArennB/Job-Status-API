from fastapi import FastAPI
from app import storage

app = FastAPI()

#Confirmation that API is running
@app.get("/")
def home():
    return {"message": "API is running"}

#Submit a job
@app.post("/jobs")
def submit():
    
    job_id = storage.next_job_id

    new_job = {
        "id": job_id,
        "status": "queued",
        "result": None
    }

    storage.jobs[job_id] = new_job

    storage.next_job_id += 1

    return new_job

#Check Job status
@app.get("/jobs/{job_id}")
def status(job_id: int):

    job = storage.jobs.get(job_id)

    if job is None:
        return{"error": "Job not found"}
    
    return job

#View job result
@app.get("/jobs/{job_id}/result")
def result(job_id: int):

    job = storage.jobs.get(job_id)

    if job is None:
        return{"error": "Job not found"}
    
    return {
        "job_id": job_id,
        "result": job["result"]
    }