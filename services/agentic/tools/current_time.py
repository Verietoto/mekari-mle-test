from datetime import datetime
from typing import Dict, Any
from .base import BaseTool

class CurrentTimeTool(BaseTool):
    """Tool to return the current UTC time."""

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "Returns the current UTC time as a string"

    def run(self, **kwargs) -> Dict[str, Any]:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return {"reply": current_time}

    def to_haystack_tool(self):
        """
        Convert this tool into a haystack.tools.Tool object
        that can be used by LLMs.
        """
        from haystack.tools import Tool

        return Tool(
            name=self.name,
            description=self.description,
            parameters={}, 
            function=self.run
        )
