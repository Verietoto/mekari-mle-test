from typing import Dict, Any, List, Optional
from time import time
from haystack import component
from agentic.nodes.routing_nodes.schemas import ConditionRoute


@component
class ConditionNode:
    """
    A conditional routing node for Haystack pipelines.
    Evaluates predefined conditions against input context and selects the first matching route.
    Adds a key named after the selected route with {"value": <forward data>}.
    """

    def __init__(self, routes: List[ConditionRoute]):

        """
        :param routes: List of ConditionRoute
        :param forward_key: Optional key from context to forward as 'value' in the route output
        """
        self.routes = routes
   

    @component.output_types(
        output_text=str,
        selected_route=Optional[str],
        output_value=Any,
        time_elapsed_sec=float,
        tokens_used=Optional[Dict[str, Any]],
        route1=str,
        route2=str,
        route3=str,
        route4=str,
    )
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time()
        selected_route = None
        output_value = None
        output_text = ""
        tokens_used = None

        result: Dict[str, Any] = {}
        
        try:
            for route in self.routes:
                # Safely evaluate each condition using the given context
                if eval(route.condition, {}, context):
                    selected_route = route.name
                    output_value = route.output_value
                    output_text = f"Matched route '{route.name}' with condition: {route.condition}"

                    # ✅ Forward selected context value if available
                    result[route.name] = route.forward['value']
                    break

            if not selected_route:
                output_text = "No matching condition found."
                selected_route = "no_match"
                result["no_match"] = {"value": None}

        except Exception as e:
            output_text = f"Error evaluating conditions: {str(e)}"
            selected_route = "error"
            result["error"] = {"value": None}

        end_time = time()

        result.update({
            "output_text": output_text,
            "selected_route": selected_route,
            "output_value": output_value,
            "time_elapsed_sec": end_time - start_time,
            "tokens_used": tokens_used,
        })

        return result
