"""ChromaDB 벡터 검색 서비스.

Gemini gemini-embedding-001 모델로 임베딩을 생성하고 ChromaDB에 저장/검색한다.
사용자별 컬렉션(`articles_{user_id}`)으로 데이터를 격리한다.
"""

import logging
from pathlib import Path
from typing import Any

import chromadb

from backend.app.config import settings

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
EMBEDDING_MODEL = "gemini-embedding-001"

_chroma_client: Any = None
_collections: dict[str, Any] = {}


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        persist_dir = settings.chroma_persist_dir
        if not Path(persist_dir).is_absolute():
            persist_dir = str(_BACKEND_DIR / persist_dir)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        logger.info("ChromaDB 클라이언트 초기화 완료: %s", persist_dir)
    return _chroma_client


def _get_collection(user_id: str):
    if user_id not in _collections:
        client = _get_chroma_client()
        collection_name = f"articles_{user_id.replace('-', '_')[:50]}"
        _collections[user_id] = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB 컬렉션 초기화: %s", collection_name)
    return _collections[user_id]


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """Gemini Embedding API로 텍스트 목록의 임베딩 벡터를 한 번에 생성한다."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
    )
    return [emb.values for emb in response.embeddings]


def add_articles_to_vector_db(user_id: str, articles: list[dict]) -> None:
    """기사 목록을 사용자별 ChromaDB 컬렉션에 배치로 저장한다."""
    if not articles:
        return

    collection = _get_collection(user_id)

    texts = [
        " ".join(filter(None, [
            art["title"],
            art.get("summary_en", ""),
            art.get("summary_ko", ""),
            " ".join(art.get("tags", [])),
        ]))
        for art in articles
    ]

    try:
        embeddings = _get_embeddings(texts)
        collection.upsert(
            ids=[art["article_id"] for art in articles],
            embeddings=embeddings,
            metadatas=[{
                "title": art["title"],
                "category": art.get("category", ""),
                "tags": ",".join(art.get("tags", [])),
            } for art in articles],
            documents=texts,
        )
        logger.debug("벡터 DB 배치 저장 완료: %d개 (user=%s)", len(articles), user_id)
    except Exception:
        logger.exception("벡터 DB 배치 저장 실패: %d개 (user=%s)", len(articles), user_id)
        raise


def search_similar(user_id: str, query: str, top_k: int = 10) -> list[dict[str, Any]]:
    """질의와 유사한 기사를 사용자별 ChromaDB 컬렉션에서 검색한다."""
    collection = _get_collection(user_id)

    try:
        count = collection.count()
        if count == 0:
            return []

        query_embedding = _get_embeddings([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        items: list[dict[str, Any]] = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                items.append({
                    "id": doc_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })

        return items
    except Exception:
        logger.exception("벡터 검색 실패: query=%s (user=%s)", query[:50], user_id)
        return []


def is_article_in_vector_db(user_id: str, article_id: str) -> bool:
    """해당 기사가 이미 사용자별 ChromaDB에 존재하는지 확인한다."""
    try:
        result = _get_collection(user_id).get(ids=[article_id], include=[])
        return len(result["ids"]) > 0
    except Exception:
        return False


def get_collection_count(user_id: str) -> int:
    """사용자별 ChromaDB에 저장된 문서 수를 반환한다."""
    try:
        return _get_collection(user_id).count()
    except Exception:
        return 0
