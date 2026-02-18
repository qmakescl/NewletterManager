from fastapi import APIRouter

from backend.app.models.chat import ChatRequest, ChatResponse
from backend.app.services.gemini import rag_query

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """RAG 채팅: 수집된 뉴스레터 기사 기반으로 질문에 답변한다."""
    result = rag_query(request.message)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )
