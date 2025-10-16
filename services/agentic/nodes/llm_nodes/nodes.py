from typing import Dict, Any, Optional, List
from time import time
from haystack import component
from haystack.utils import Secret
from haystack.dataclasses import ChatMessage
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.tools import Tool
import tiktoken
from config import get_settings
from agentic.nodes.llm_nodes.schemas import LLMInput, LLMOutput


@component
class LLMNode:
    """
    General-purpose LLM node for reasoning, answering, or tool-assisted tasks.
    Compatible with Haystack Pipelines.
    """

    def __init__(
        self,
        tools: Optional[List[Tool]] = None,
        max_memory: int = 10,
        model: str = "gpt-4o-mini",
        max_iterations: int = 5,
        streaming_callback: Optional[callable] = None,  # type: ignore
        system_prompt: str = "",
        chat_history: Optional[List[ChatMessage]] = None  # ✅ optional external history
    ):
        self.api_key = Secret.from_token(get_settings().open_ai_api_key)
        self.max_memory = max_memory
        self.model = model
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.streaming_callback = streaming_callback
        self.system_prompt = system_prompt

        # --- Tokenizer ---
        try:
            self.encoder = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

        # --- Agent setup ---
        chat_gen = OpenAIChatGenerator(
            model=self.model,
            api_key=self.api_key,
            streaming_callback=self.streaming_callback,
            generation_kwargs={
                "temperature": 0,
                "top_p": 1,
            },
        )

        self.agent = Agent(
            chat_generator=chat_gen,
            tools=self.tools,
            max_agent_steps=self.max_iterations,
            streaming_callback=self.streaming_callback,
        )

        # Persistent conversation history
        self.chat_history: List[ChatMessage] = chat_history if chat_history is not None else []

    # ---------------------------------------------------------
    #                  Component Output Types
    # ---------------------------------------------------------
    @component.output_types(
        output_text=str,
        tools_used=Optional[List[Dict[str, Any]]],
        time_elapsed_sec=float,
        tokens_used=Optional[Dict[str, int]],
        last_message=Optional[ChatMessage],
    )
    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Executes the LLM process via Agent.
        """

        validated_input = LLMInput(user_prompt=user_prompt)

        # Build messages
        user_message = ChatMessage.from_user(validated_input.user_prompt)
        system_message = ChatMessage.from_system(self.system_prompt)
        messages = [system_message] + self.chat_history[-self.max_memory:] + [user_message]

        # Append current user message to history
        self.chat_history.append(user_message)

        # Run agent
        start_time = time()
        result = self.agent.run(messages=messages)
        end_time = time()

        # Extract results
        last_message: Optional[ChatMessage] = result.get("last_message")
        output_text = last_message.text if last_message and last_message.text else ""

        if last_message:
            self.chat_history.append(last_message)

        # Track tools used
        tools_used = []
        for msg in result.get("messages", []):
            if msg.tool_call_result:
                tools_used.append({
                    "tool_name": msg.tool_call_result.origin.tool_name,
                    "args": getattr(msg.tool_call_result.origin, "arguments", None),
                    "result": msg.tool_call_result.result,
                    "error": getattr(msg.tool_call_result, "error", None)
                })

        # Token accounting
        prompt_tokens = sum(len(self.encoder.encode(m.text)) for m in messages if m.text)
        completion_tokens = len(self.encoder.encode(output_text))
        total_tokens = prompt_tokens + completion_tokens

        # --- Return ---
        return LLMOutput(
            output_text=output_text,
            tools_used=tools_used,
            time_elapsed_sec=end_time - start_time,
            tokens_used={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
            last_message=last_message,
        ).model_dump()