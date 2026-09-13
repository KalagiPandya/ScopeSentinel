from typing import List, Dict, Optional
import uuid
import re

COLLECTION_NAME = "requirements_local"
VECTOR_SIZE = 384


def _token_similarity(text1: str, text2: str) -> float:
    """Fast Jaccard token similarity for semantic comparison."""
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)


def create_collection_if_not_exists():
    try:
        from app.config import settings
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
    except Exception as e:
        print(f"[Qdrant Notice] Running with database similarity fallback: {e}")


def store_requirement(requirement_id: str, project_id: str, text: str) -> str:
    point_id = str(uuid.uuid4())
    try:
        from app.config import settings
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct

        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=[0.0] * VECTOR_SIZE,
                    payload={"requirement_id": requirement_id, "project_id": project_id, "text": text},
                )
            ],
        )
    except Exception:
        pass
    return point_id


def search_similar(text: str, project_id: str, top_k: int = 3, score_threshold: float = None) -> List[Dict]:
    try:
        from app.config import settings
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=[0.0] * VECTOR_SIZE,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=Filter(must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))]),
        )
        if results:
            return [
                {"requirement_id": r.payload["requirement_id"], "text": r.payload["text"], "score": round(r.score, 4)}
                for r in results
            ]
    except Exception:
        pass

    # Database SQL fallback similarity calculation
    try:
        from app.database import SessionLocal
        from app.models.requirement import Requirement

        db = SessionLocal()
        reqs = db.query(Requirement).filter(Requirement.project_id == project_id).all()
        matches = []
        for r in reqs:
            sim = _token_similarity(text, r.text)
            if score_threshold is None or sim >= score_threshold:
                matches.append({"requirement_id": str(r.id), "text": r.text, "score": round(sim, 4)})
        db.close()
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k]
    except Exception as e:
        print(f"[Similarity Fallback Error] {e}")
        return []


def delete_requirement(point_id: str):
    try:
        from app.config import settings
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
        client.delete(collection_name=COLLECTION_NAME, points_selector=[point_id])
    except Exception:
        pass