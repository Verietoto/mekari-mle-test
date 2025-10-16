from haystack import Pipeline
from agentic.nodes.guardtrail_nodes.nodes import GuardrailNode
from agentic.nodes.start_nodes.nodes import StartNode
from agentic.nodes.routing_nodes.nodes import ConditionNode
from agentic.nodes.routing_nodes.schemas import ConditionRoute
from agentic.nodes.convertion_nodes.nodes import ConvertToDictNode
from agentic.nodes.llm_nodes.nodes import LLMNode
from agentic.nodes.answer_nodes.nodes import AnswerNode
from config import get_settings
from agentic.tools.current_time import CurrentTimeTool
from agentic.tools.fraud_query import FraudQueryTool, FraudSummaryTool
from agentic.tools.fraud_rag import PDFRagTool
import logging
import yaml
import os
# Suppress info messages from Haystack agents
logging.getLogger("haystack").setLevel(logging.ERROR)

def load_prompts(file_name="prompt.yaml"):
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Build full path to the YAML file
    file_path = os.path.join(current_dir, file_name)

    # Load YAML
    with open(file_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    return prompts

prompts = load_prompts()
guardrail_prompt = prompts["guardrail_prompt"]
non_related_llm_prompt = prompts["non_related_llm_prompt"]
agent_query_prompt = prompts["agent_query_prompt"]

class QnaWorkflow:
    """
    Question and answering workflow with sentiment + flag routing.
    Includes streaming support for agentic LLM node.
    """

    def __init__(self, user_query: str, chat_history: list, streaming_callback: callable): # type: ignore
        settings = get_settings()
        self.openai_api_key = settings.open_ai_api_key
        self.default_model = "gpt-4o-mini"
        self.user_query = user_query
        self.streaming_callback = streaming_callback
        self.chat_history = chat_history


        # System prompt for GuardrailNode
        self.guardrail_prompt = prompts["guardrail_prompt"]
        self.non_related_llm_prompt = prompts["non_related_llm_prompt"]
        self.agent_query = prompts["agent_query_prompt"]

    # -------------------------------------------------------
    # Build Pipeline
    # -------------------------------------------------------
    def get_pipeline(self) -> Pipeline:
        start_node = StartNode(user_query=self.user_query)
        guardrail_node = GuardrailNode(
            max_memory=5,
            model=self.default_model,
            system_prompt=self.guardrail_prompt,
            chat_history=self.chat_history,
            
        )

        # Routes
        alert_route = ConditionRoute(
            name="route1",
            condition="flagged == True or sentiment == 'negative'",
            output_value="{{ output_text }}",
            description="Route when input is flagged or sentiment is negative.",
            forward={"value": self.user_query},
        )

        normal_route = ConditionRoute(
            name="route2",
            condition="flagged == False and sentiment != 'negative'",
            output_value="{{ output_text }}",
            description="Route when input is safe and sentiment is not negative.",
            forward={"value": self.user_query},
        )

        # Route node
        route_node = ConditionNode(routes=[alert_route, normal_route])

        # Convert structured output
        convertion_nodes = ConvertToDictNode()

        # Non-related topic LLM
        non_related_llm = LLMNode(
            model=self.default_model,
            system_prompt=self.non_related_llm_prompt,
            streaming_callback=self.streaming_callback,
            chat_history=self.chat_history
        )

        # ✅ Agentic LLM with streaming
        agentic_llm = LLMNode(
            model=self.default_model,
            system_prompt=self.agent_query,
            tools=[
                CurrentTimeTool().to_haystack_tool(),
                FraudQueryTool().to_haystack_tool(),
                FraudSummaryTool().to_haystack_tool(),
                PDFRagTool().to_haystack_tool(),
            ],
            streaming_callback=self.streaming_callback,
            chat_history=self.chat_history
        )

        # Build pipeline
        pipeline = Pipeline()
        pipeline.add_component(instance=start_node, name="start_node")
        pipeline.add_component(instance=guardrail_node, name="guardtrail_node")
        pipeline.add_component(instance=convertion_nodes, name="convert_structured")
        pipeline.add_component(instance=route_node, name="condition_node")
        pipeline.add_component(instance=non_related_llm, name="non_related_llm")
        pipeline.add_component(instance=agentic_llm, name="agentic_llm")

        # Connect flow
        pipeline.connect("start_node.query_text", "guardtrail_node.user_prompt")
        pipeline.connect("guardtrail_node.structured_output", "convert_structured.data")
        pipeline.connect("convert_structured.output", "condition_node.context")

        # Routes 1
        answer_node1 = AnswerNode()
        pipeline.add_component(instance=answer_node1, name="answer_node1")
        pipeline.connect("condition_node.route1", "non_related_llm.user_prompt")
        pipeline.connect("non_related_llm.output_text", "answer_node1.final_answer")

        # Route 2
        answer_node2 = AnswerNode()
        pipeline.add_component(instance=answer_node2, name="answer_node2")
        pipeline.connect("condition_node.route2", "agentic_llm.user_prompt")
        pipeline.connect("agentic_llm.output_text", "answer_node2.final_answer")

        return pipeline

    # -------------------------------------------------------
    # Run Pipeline
    # -------------------------------------------------------
    def run(self) -> dict:
        """
        Run the Guardrail pipeline with streaming if available.
        """
        pipeline = self.get_pipeline()
        return pipeline.run({})
