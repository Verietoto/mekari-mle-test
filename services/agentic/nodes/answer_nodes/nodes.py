from haystack import component
from typing import Dict, Any, Optional

@component
class AnswerNode:
    """
    Collects final output from multiple branches and returns a single string.
    """

    @component.output_types(
        final_answer=str,
    )
    def run(self, final_answer: str) -> Dict[str, Any]:
        """
        Accepts arbitrary inputs from previous nodes and returns a single string.
        Priority order: agentic_llm > non_related_llm > any other.
        """
      

        return {"final_answer": final_answer}
