from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    result: str | None


class JobResultResponse(BaseModel):
    job_id: int
    status: str
    result: str | None
