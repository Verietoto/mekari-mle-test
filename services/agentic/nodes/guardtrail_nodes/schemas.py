from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class GuardTrailInput(BaseModel):
    system_prompt: str = Field(..., description="System prompt for the LLM")
    user_prompt: str = Field(..., description="User prompt for the LLM")
    model: str = Field("gpt-4o-mini", description="OpenAI model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature for generation")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling probability")
    max_memory: int = Field(0, ge=0, le=50, description="Maximum chat history")


# Define the structured output model the LLM must follow
class GuardTrailStructuredOutput(BaseModel):
    summary: str = Field(..., description="Brief summary of the user query or context related to topic or no based on system prompt")
    sentiment: str = Field(..., description="Sentiment detected in the user query, e.g., positive, neutral, negative")
    flagged: bool = Field(..., description="Indicates if the input should be flagged for review or alerts based on system prompt")


class GuardTrailOutput(BaseModel):
    output_text: str
    time_elapsed_sec: float
    tokens_used: Optional[Dict[str, Any]] = Field(
        None, description="Token usage info returned by the model. Can be nested.")
    structured_output: GuardTrailStructuredOutput
    