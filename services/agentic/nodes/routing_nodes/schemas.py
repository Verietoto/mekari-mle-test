# agentic/nodes/condition_nodes/schemas.py
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class ConditionRoute(BaseModel):
    name: str
    condition: str = Field(..., description="Python expression to evaluate, e.g. 'x < 2'")
    output_value: Any
    description: Optional[str] = None
    forward: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional extra data to forward if this route is selected."
    )
