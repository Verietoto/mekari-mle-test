# agentic/nodes/utils_nodes/convert_to_dict_node.py
from haystack import component
from typing import Any, Dict

@component
class ConvertToDictNode:
    """
    Converts Pydantic model-like output to dict so it can be used in next node.
    """
    @component.output_types(output=Dict[str, Any])
    def run(self, data: Any) -> Dict[str, Any]:
        if hasattr(data, "model_dump"):
            return {"output": data.model_dump()}
        return {"output": data}
