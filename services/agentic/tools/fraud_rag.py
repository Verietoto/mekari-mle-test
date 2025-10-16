from typing import Any, Dict, List, Optional
from agentic.tools.base import BaseTool
from business.usecase.rag.rag import TreeBasedRag
from config import get_settings


class PDFRagTool(BaseTool):
    """Tool for retrieving relevant PDF text chunks based on a query using embeddings."""

    def __init__(self, threshold: float = 0.55, collection_name: str = "pdf_collection"):
        self.rag = TreeBasedRag(
            threshold=threshold,
            collection_name=collection_name,
            pdf_path="../raw_dataset/Bhatla.pdf"
        )

    @property
    def name(self) -> str:
        return "pdf_rag_tools"

    @property
    def description(self) -> str:
        return """
Tool name: PDfRagTools
Purpose: Retrieve relevant sections of a knowledge based on user querys.

Arguments:
- query: Text query to search within the PDF collection.


Returns:
- page_text: Dictionary mapping page number -> extracted knowledge from pdf
"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Query string to search in PDF"},
            },
            "required": ["query"]
        }

    def run(self, **kwargs) -> Dict[str, Any]:
        query: str = kwargs.get("query") # type: ignore
        if not query:
            raise ValueError("The 'query' parameter is required.")


        results = self.rag.execute(query=query)
        return results['page_text']
