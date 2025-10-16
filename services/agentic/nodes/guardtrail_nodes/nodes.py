from typing import Optional, Dict, Any
from time import time
from haystack import component
from haystack.utils import Secret
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from agentic.nodes.guardtrail_nodes.schemas import (
    GuardTrailInput,
    GuardTrailOutput,
    GuardTrailStructuredOutput,
)
from config import get_settings
import json

@component
class GuardrailNode:
    """
    Guardrail LLM node for pipelines.
    - Configuration (model, prompt, parameters) is set at init time.
    - Optional chat_history can be provided at init.
    """

    def __init__(
        self,
        system_prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0,
        top_p: float = 1.0,
        max_memory: int = 0,
        chat_history: Optional[list[ChatMessage]] = None,  # ✅ optional external history
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_memory = max_memory

        settings = get_settings()
        self.api_key = Secret.from_token(settings.open_ai_api_key)

        # Use provided history or initialize empty list
        self.chat_history: list[ChatMessage] = chat_history if chat_history is not None else []

    @component.output_types(
        output_text=str,
        structured_output=GuardTrailStructuredOutput,
        time_elapsed_sec=float,
        tokens_used=Optional[Dict[str, int]],
    )
    def run(self, user_prompt: str) -> Dict[str, Any]:
        validated_input = GuardTrailInput(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            model=self.model,
            temperature=self.temperature,
            top_p=self.top_p,
            max_memory=self.max_memory,
        )

        system_message = ChatMessage.from_system(validated_input.system_prompt)
        user_message = ChatMessage.from_user(validated_input.user_prompt)

        # Use the node's internal chat_history
        messages = [system_message, user_message] + self.chat_history[-validated_input.max_memory:]

        generator = OpenAIChatGenerator(
            model=validated_input.model,
            api_key=self.api_key,
            generation_kwargs={
                "temperature": validated_input.temperature,
                "top_p": validated_input.top_p,
                "response_format": GuardTrailStructuredOutput,
            },
        )

        start_time = time()
        response = generator.run(messages=messages)
        end_time = time()

        assistant_message = response["replies"][0]

        # Always append to the internal history
        self.chat_history.append(user_message)
        self.chat_history.append(assistant_message)

        output_text = assistant_message.text or ""
        tokens_used = assistant_message.meta.get("usage") or None

        try:
            structured_output = json.loads(output_text)
        except Exception as e:
            structured_output = GuardTrailStructuredOutput(
                summary=str(e),
                sentiment="neutral",
                flagged=True,
            )

        return GuardTrailOutput(
            output_text=output_text,
            time_elapsed_sec=end_time - start_time,
            tokens_used=tokens_used,
            structured_output=structured_output,
        ).model_dump()
