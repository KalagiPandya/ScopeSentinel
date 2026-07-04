"""
Core change detection logic.
Given a new requirement text, finds whether it is:
  - no_change   : same requirement already exists (similarity >= 0.92)
  - modification: existing requirement was modified (similarity 0.60-0.92)
  - new_addition: brand new requirement (similarity < 0.60)
"""
from typing import List, Dict
from app.services.diff_service import get_change_summary

SAME_THRESHOLD     = 0.92   # above this = same req, no change
MODIFIED_THRESHOLD = 0.60   # between this and SAME = modification


def classify_change(score: float) -> str:
    if score >= SAME_THRESHOLD:
        return "no_change"
    elif score >= MODIFIED_THRESHOLD:
        return "modification"
    else:
        return "new_addition"


def detect_change(new_text: str, project_id: str) -> Dict:
    from app.services.qdrant_service import search_similar

    matches = search_similar(text=new_text, project_id=project_id, top_k=1, score_threshold=0.3)

    if not matches:
        return {"change_type": "new_addition", "similar_requirement": None,
                "similarity_score": 0.0, "word_diff": None}

    best  = matches[0]
    score = best["similarity_score"]
    change_type = classify_change(score)

    word_diff = None
    if change_type == "modification":
        word_diff = get_change_summary(old_text=best["text"], new_text=new_text)

    return {
        "change_type": change_type,
        "similar_requirement": best,
        "similarity_score": score,
        "word_diff": word_diff,
    }


def batch_detect_changes(texts: List[str], project_id: str) -> List[Dict]:
    """Run detection on a list — returns only actual changes (skips no_change)."""
    results = []
    for text in texts:
        r = detect_change(text, project_id)
        if r["change_type"] != "no_change":
            r["new_text"] = text
            results.append(r)
    return results
