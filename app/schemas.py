from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    result: str | None
    submitted_at: datetime
    completed_at: datetime | None


class JobResultResponse(BaseModel):
    job_id: int
    status: str
    result: str | None
    completed_at: datetime | None
