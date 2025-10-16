from typing import Callable, List, Dict, Any, Optional
from contracts.errors import AppError
from agentic.workflow.qna_flow.qna_flow import QnaWorkflow
from haystack.dataclasses import ChatMessage, StreamingChunk
from haystack.components.generators.utils import _convert_streaming_chunks_to_chat_message, print_streaming_chunk
from ..abc import Usecase
import time


class AgenticUsecase(Usecase):
    """
    Usecase to handle user queries via the Agentic QnA workflow.
    Supports chat history passed externally, streaming, and metadata tracking.
    """

    def __init__(self) -> None:
        # Internal fallback chat history if none is provided
        self.chat_history: List[ChatMessage] = []
        self.chunks: List[StreamingChunk] = []
        self.answer: str = ""
        self.answer_stream: str = ""

    def collect_streaming_chunk(self, chunk: StreamingChunk) -> None:
        """
        Callback function to handle and collect streaming output chunks into self.answer_text.

        Accumulates tool calls, tool results, assistant content, and reasoning into a single variable.
        """
        if not hasattr(self, "answer_stream"):
            self.answer_stream = ""  # initialize if not already

        chunk_text = ""

        if chunk.start and chunk.index and chunk.index > 0:
            chunk_text += "\n\n"

        ## Tool Call streaming
        if chunk.tool_calls:
            for tool_call in chunk.tool_calls:
                if chunk.start:
                    if chunk.index and tool_call.index > chunk.index:
                        chunk_text += "\n\n"
                    chunk_text += f"[TOOL CALL]\nTool: {tool_call.tool_name} \nArguments: "
                if tool_call.arguments:
                    chunk_text += str(tool_call.arguments)

        ## Tool Call Result streaming
        if chunk.tool_call_result:
            chunk_text += f"[TOOL RESULT]\n{chunk.tool_call_result.result}"

        ## Normal content streaming
        if chunk.content:
            if chunk.start:
                chunk_text += "[ASSISTANT]\n"
            chunk_text += chunk.content

        ## Reasoning content streaming
        if chunk.reasoning:
            if chunk.start:
                chunk_text += "[REASONING]\n"
            chunk_text += chunk.reasoning.reasoning_text

        ## End of message spacing
        if chunk.finish_reason is not None:
            chunk_text += "\n\n"

        # Append the processed chunk text to self.answer_text
        self.answer_stream += chunk_text
     


    def stream_callback(self, chunk: StreamingChunk):
        """
        Streaming callback called by the QnA workflow for each chunk.
        Appends the chunk to self.chunks and accumulates text in self.answer.
        """
        self.collect_streaming_chunk(chunk)

    
    def execute(
        self,
        user_query: str,
        chat_history: Optional[List[ChatMessage]] = None,
        streaming_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a user query using QnaWorkflow.
        `chat_history` can be passed from API layer to maintain session.
        """

        if not user_query:
            raise AppError(status_code=400, code="empty_query", message="Query cannot be empty.")

        # Use provided chat history or internal fallback
        if chat_history is None:
            chat_history = self.chat_history

        # Reset streaming state before execution
        self.chunks = []
        self.answer = ""

        # Track overall timing
        start_time = time.perf_counter()

        # Initialize workflow with chat history
        workflow = QnaWorkflow(
            user_query=user_query,
            chat_history=chat_history,
            streaming_callback=streaming_callback
        )

        # Run pipeline
        result = workflow.run()

        end_time = time.perf_counter()

        # Gather final answer
        final_answer = self.answer
        # Update chat history
        chat_history.append(ChatMessage.from_user(user_query))
        chat_history.append(ChatMessage.from_assistant(final_answer))

        # Gather overall token usage if available
        total_time = 0
        total_tokens = 0
        for node_name, node_output in result.items():
            # Add time elapsed
            node_time = node_output.get("time_elapsed_sec", 0.0)
            total_time += node_time

            # Add total tokens from node if available
            tokens_used = node_output.get("tokens_used")
            if tokens_used and "total_tokens" in tokens_used:
                total_tokens += tokens_used["total_tokens"]


        return {
            "final_answer": final_answer,
            "overall_time_ms": round(total_time, 2),
            "tokens_used": total_tokens,
            "chat_history": chat_history,
        }
