"""
Agent 6 — Risk Analyzer

For each detected change (with impact data from Agent 5), calculates a
risk score 0-100 and risk level (low/medium/high/critical) using an LLM
with chain-of-thought reasoning over:

  - change_type (new_addition is riskier than modification)
  - similarity_score (lower similarity = bigger change = riskier)
  - impact.total_affected (more affected modules = riskier)
  - depth_1 count (direct hits are most dangerous)

Falls back to a deterministic formula if the LLM call fails, so the
pipeline never breaks.
"""
import json
from app.agent.state import AgentState


RISK_PROMPT = """You are a software project risk analyst. A requirement
changed in a project. Assess the RISK this change poses to the project
timeline and quality.

Change type: {change_type}
New requirement text: "{new_text}"
Similarity to previous version: {similarity:.0%}
Total modules/components affected (from dependency graph): {total_affected}
Directly affected modules (depth 1): {depth_1_names}

Consider:
- new_addition with many affected modules = higher risk (scope creep)
- modification with low similarity = bigger rewrite = higher risk
- many depth_1 modules = immediate dev/test rework needed

Return ONLY valid JSON, no markdown:
{{
  "risk_score": <integer 0-100>,
  "risk_level": "<low|medium|high|critical>",
  "justification": "<1-2 sentence plain English explanation>",
  "recommended_action": "<1 short actionable sentence>"
}}

risk_level bands: low=0-25, medium=26-50, high=51-75, critical=76-100
"""


def _fallback_score(change: dict) -> dict:
    """Deterministic backup scoring if LLM call fails."""
    impact = change.get("impact", {})
    total_affected = impact.get("total_affected", 0)
    similarity = change.get("similarity_score", 0.5)
    change_type = change.get("change_type", "modification")

    score = 0
    score += 30 if change_type == "new_addition" else 15
    score += min(total_affected * 8, 40)
    score += int((1 - similarity) * 30)
    score = min(score, 100)

    if score >= 76:
        level = "critical"
    elif score >= 51:
        level = "high"
    elif score >= 26:
        level = "medium"
    else:
        level = "low"

    return {
        "risk_score": score,
        "risk_level": level,
        "justification": (
            f"{change_type.replace('_', ' ').title()} affecting {total_affected} "
            f"module(s) with {similarity:.0%} similarity to previous version."
        ),
        "recommended_action": "Review affected modules before next sprint planning.",
    }


def _call_llm(prompt: str) -> str:
    from openai import OpenAI
    from app.config import settings

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


def risk_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Agent 6.
    Reads state['detected_changes'] (with 'impact' from Agent 5),
    adds 'risk' key to each change dict:

      risk = {
        "risk_score": 0-100,
        "risk_level": "low|medium|high|critical",
        "justification": "...",
        "recommended_action": "..."
      }
    """
    changes = state.get("detected_changes", [])
    errors = list(state.get("errors", []))

    for change in changes:
        impact = change.get("impact", {})
        depth_1_names = [m["name"] for m in impact.get("depth_1", [])]

        try:
            prompt = RISK_PROMPT.format(
                change_type=change.get("change_type", "unknown"),
                new_text=change.get("new_text", ""),
                similarity=change.get("similarity_score", 0.0),
                total_affected=impact.get("total_affected", 0),
                depth_1_names=", ".join(depth_1_names) if depth_1_names else "none",
            )
            raw = _call_llm(prompt)
            parsed = _parse_json(raw)

            if not parsed or "risk_score" not in parsed:
                parsed = _fallback_score(change)

        except Exception as e:
            parsed = _fallback_score(change)
            errors.append(f"risk_node: LLM failed, used fallback: {str(e)}")

        # clamp and normalize
        score = int(max(0, min(100, parsed.get("risk_score", 0))))
        level = parsed.get("risk_level", "low")
        if level not in ("low", "medium", "high", "critical"):
            level = _fallback_score(change)["risk_level"]

        change["risk"] = {
            "risk_score": score,
            "risk_level": level,
            "justification": parsed.get("justification", ""),
            "recommended_action": parsed.get("recommended_action", ""),
        }

    return {**state, "detected_changes": changes, "errors": errors}
