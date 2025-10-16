from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Dict, List, Any

from business.usecase.rag.rag import TreeBasedRag
from contracts.response import SuccessEnvelope
from contracts.errors import AppError

router = APIRouter(prefix="/rag/v1", tags=["RAG PDF"])

# -------------------------------
# Request & Response Models
# -------------------------------
class RagQueryRequest(BaseModel):
    query: str


class RagQueryResponse(BaseModel):
    page_text: Dict[int, str]    # page_number -> text


# -------------------------------
# Initialize Usecase
# -------------------------------
rag_usecase = TreeBasedRag(
    threshold=0.55,
    pdf_path="../raw_dataset/Bhatla.pdf"
)


# -------------------------------
# Handler
# -------------------------------
class RagHandler:

    def __init__(self, usecase: TreeBasedRag):
        self._usecase = usecase

    def handle(self, query: str) -> RagQueryResponse:
        try:
            result:dict = self._usecase.execute(query)
            return RagQueryResponse(
                page_text=result["page_text"]
            )
        except Exception as e:
            raise AppError(message=f"Failed to execute RAG query: {e}")


rag_handler = RagHandler(rag_usecase)


# -------------------------------
# Query Endpoint
# -------------------------------
@router.post("/query", response_model=SuccessEnvelope[RagQueryResponse])
async def rag_query_endpoint(request: Request, body: RagQueryRequest):
    """
    Query the PDF using TreeBasedRag RAG system.
    Returns filtered nodes and PDF text by pages.
    """
    result = rag_handler.handle(body.query)
    return SuccessEnvelope[RagQueryResponse](data=result)