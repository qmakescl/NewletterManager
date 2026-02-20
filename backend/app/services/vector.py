"""ChromaDB 벡터 검색 서비스.

Gemini gemini-embedding-001 모델로 임베딩을 생성하고 ChromaDB에 저장/검색한다.
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
_collection: Any = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        persist_dir = settings.chroma_persist_dir
        if not Path(persist_dir).is_absolute():
            persist_dir = str(_BACKEND_DIR / persist_dir)

        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _collection = _chroma_client.get_or_create_collection(
            name="articles",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB 컬렉션 초기화 완료: %s", persist_dir)
    return _collection


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """Gemini Embedding API로 텍스트 목록의 임베딩 벡터를 한 번에 생성한다."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
    )
    return [emb.values for emb in response.embeddings]


def add_articles_to_vector_db(articles: list[dict]) -> None:
    """기사 목록을 ChromaDB에 배치로 저장한다 (이미 존재하면 업데이트).

    Args:
        articles: 각 항목은 article_id, title, summary_en, summary_ko, category, tags 키를 가진 dict
    """
    if not articles:
        return

    collection = _get_collection()

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
        logger.debug("벡터 DB 배치 저장 완료: %d개", len(articles))
    except Exception:
        logger.exception("벡터 DB 배치 저장 실패: %d개", len(articles))
        raise


def search_similar(query: str, top_k: int = 10) -> list[dict[str, Any]]:
    """질의와 유사한 기사를 ChromaDB에서 검색한다."""
    collection = _get_collection()

    try:
        query_embedding = _get_embeddings([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
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
        logger.exception("벡터 검색 실패: query=%s", query[:50])
        return []


def is_article_in_vector_db(article_id: str) -> bool:
    """해당 기사가 이미 ChromaDB에 존재하는지 확인한다."""
    try:
        result = _get_collection().get(ids=[article_id], include=[])
        return len(result["ids"]) > 0
    except Exception:
        return False


def get_collection_count() -> int:
    """ChromaDB에 저장된 문서 수를 반환한다."""
    try:
        return _get_collection().count()
    except Exception:
        return 0
