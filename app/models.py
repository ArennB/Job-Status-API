from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base

#Creates the structure of our tables in SQLAlchemy
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(String, nullable=False)
    result = Column(String, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)