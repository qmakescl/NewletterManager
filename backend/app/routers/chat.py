from fastapi import APIRouter, Depends

from backend.app.dependencies import get_current_user
from backend.app.models.chat import ChatRequest, ChatResponse
from backend.app.services.gemini import rag_query

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """RAG 채팅: 수집된 뉴스레터 기사 기반으로 질문에 답변한다."""
    result = rag_query(user["id"], request.message)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )
