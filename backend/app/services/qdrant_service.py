from typing import List
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from sentence_transformers import SentenceTransformer


# =========================
# CONFIG
# =========================

COLLECTION_NAME = "requirements_local"
VECTOR_SIZE = 384  # sentence-transformers model size


# =========================
# LOAD MODEL (LOCAL - FREE)
# =========================

_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> List[float]:
    return _model.encode(text).tolist()


# =========================
# QDRANT CLIENT
# =========================

def _qdrant():
    from app.config import settings
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT
    )


# =========================
# CREATE COLLECTION
# =========================

def create_collection_if_not_exists():
    client = _qdrant()

    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            ),
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


# =========================
# STORE REQUIREMENT
# =========================

def store_requirement(requirement_id: str, project_id: str, text: str) -> str:
    point_id = str(uuid.uuid4())

    _qdrant().upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=get_embedding(text),
                payload={
                    "requirement_id": requirement_id,
                    "project_id": project_id,
                    "text": text,
                },
            )
        ],
    )

    return point_id


# =========================
# SEARCH SIMILAR
# =========================

def search_similar(text: str, project_id: str, top_k: int = 3):
    results = _qdrant().search(
        collection_name=COLLECTION_NAME,
        query_vector=get_embedding(text),
        limit=top_k,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=project_id)
                )
            ]
        ),
    )

    return [
        {
            "requirement_id": r.payload["requirement_id"],
            "text": r.payload["text"],
            "score": round(r.score, 4),
        }
        for r in results
    ]


# =========================
# DELETE REQUIREMENT
# =========================

def delete_requirement(point_id: str):
    _qdrant().delete(
        collection_name=COLLECTION_NAME,
        points_selector=[point_id],
    )