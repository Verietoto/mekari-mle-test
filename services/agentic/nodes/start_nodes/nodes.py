from typing import Dict, Any, Optional
from time import time
from haystack import component
from agentic.nodes.start_nodes.schemas import StartInput, StartOutput


@component
class StartNode:
    """
    Entry point node for pipelines.
    Accepts a predefined user query (passed during initialization),
    validates and normalizes it for downstream nodes.
    """

    def __init__(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize StartNode with a fixed query, session ID, and metadata.
        """
        self.user_query = user_query.strip()
        self.session_id = session_id
        self.metadata = metadata or {}

    @component.output_types(
        query_text=str,
        session_id=Optional[str],
        metadata=Optional[Dict[str, Any]],
        time_elapsed_sec=float,
    )
    def run(self) -> Dict[str, Any]:
        """
        Runs the node and outputs the initialized query and metadata.
        """
        start_time = time()

        # Validate structured input
        validated_input = StartInput(
            user_query=self.user_query,
            session_id=self.session_id,
            metadata=self.metadata,
        )

        end_time = time()

        # Return structured output
        return StartOutput(
            query_text=validated_input.user_query,
            session_id=validated_input.session_id,
            metadata=validated_input.metadata,
            time_elapsed_sec=end_time - start_time,
        ).model_dump()
