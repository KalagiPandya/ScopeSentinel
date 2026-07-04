from fastapi import APIRouter, Depends
from pydantic import BaseModel
from uuid import UUID
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/search", tags=["Search & Detection"])


class SearchRequest(BaseModel):
    project_id: UUID
    text: str
    top_k: int = 3
    threshold: float = 0.5


class DetectRequest(BaseModel):
    project_id: UUID
    text: str


class DiffRequest(BaseModel):
    old_text: str
    new_text: str


@router.post("/similar",
             summary="Find semantically similar requirements (needs OpenAI key)")
def search_similar_requirements(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Vector search — finds existing requirements similar to the query
    even when the wording is completely different.
    Requires OPENAI_API_KEY in .env
    """
    from app.services.qdrant_service import search_similar
    results = search_similar(
        text=data.text,
        project_id=str(data.project_id),
        top_k=data.top_k,
        score_threshold=data.threshold,
    )
    return {"query": data.text, "results": results, "count": len(results)}


@router.post("/detect-change",
             summary="Detect if new text is a requirement change (needs OpenAI key)")
def detect_requirement_change(
    data: DetectRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Core change detection.
    Returns: no_change | modification | new_addition
    For modifications, returns word_diff showing exactly what changed.
    Requires OPENAI_API_KEY in .env
    """
    from app.services.change_detection_service import detect_change
    result = detect_change(new_text=data.text, project_id=str(data.project_id))

    messages = {
        "no_change":    f"Already exists (similarity {result['similarity_score']:.0%}). No action needed.",
        "modification": f"Existing requirement modified (similarity {result['similarity_score']:.0%}). See word_diff.",
        "new_addition": f"Brand new requirement (best match {result['similarity_score']:.0%}).",
    }
    return {
        "input_text":          data.text,
        "change_type":         result["change_type"],
        "similarity_score":    result["similarity_score"],
        "similar_requirement": result.get("similar_requirement"),
        "word_diff":           result.get("word_diff"),
        "explanation":         messages[result["change_type"]],
    }


@router.post("/diff",
             summary="Word-level diff between two texts (no API key needed)")
def word_diff(data: DiffRequest, current_user: User = Depends(get_current_user)):
    """
    Compare two requirement texts and show which words were added/removed.
    Uses Myers diff algorithm. Works offline — no OpenAI key needed.
    """
    from app.services.diff_service import get_change_summary
    return get_change_summary(old_text=data.old_text, new_text=data.new_text)
