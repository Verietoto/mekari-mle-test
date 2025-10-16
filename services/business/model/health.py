from pydantic import BaseModel
from typing import Optional


class HealthModel(BaseModel):
    status: str
    uptime_seconds: Optional[float] = None
