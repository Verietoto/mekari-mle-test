from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

class BaseNode(ABC):
    InputType: Optional[Type[BaseModel]] = None
    OutputType: Optional[Type[BaseModel]] = None

    def validate_input(self, data: Dict[str, Any]) -> Any:
        """
        Returns a Pydantic model instance if InputType is set,
        otherwise returns the raw dictionary.
        """
        if self.InputType:
            return self.InputType(**data)
        return data

    @abstractmethod
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
