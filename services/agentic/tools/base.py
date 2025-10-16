from abc import ABC, abstractmethod
from typing import Any, Dict
from haystack.tools import Tool

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool"""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what the tool does"""

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Run the tool with parameters"""

    def to_haystack_tool(self) -> Tool:
        """
        Convert this BaseTool subclass into a haystack.tools.Tool
        that can be used by LLMNode or OpenAIChatGenerator.
        """
        # If the tool defines a parameters property, use it; otherwise default to empty dict
        parameters = getattr(self, "parameters", {})
        
        return Tool(
            name=self.name,
            description=self.description,
            parameters=parameters,
            function=self.run
        )

