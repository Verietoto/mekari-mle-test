from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class StartInput(BaseModel):
    user_query: str = Field(..., description="User query text")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class StartOutput(BaseModel):
    query_text: str
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    time_elapsed_sec: float
