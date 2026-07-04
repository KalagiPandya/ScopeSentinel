"""
Agent 1 — Requirement Extractor

Reads raw text (meeting transcript, email, document, Jira ticket) and
identifies individual software requirement statements using an LLM.

Uses few-shot prompting + structured JSON output so results are
consistent and parseable.
"""
import json
from app.agent.state import AgentState, ExtractedRequirement


EXTRACTION_PROMPT = """You are a requirements analyst AI. Your job is to read the
text below and extract every individual software REQUIREMENT statement.

A requirement describes something the system MUST do, SHOULD do, or a
constraint it must satisfy. Ignore greetings, small talk, and unrelated chatter.

For each requirement found, classify its type:
- "functional": describes a feature/behavior (e.g. "users can reset password")
- "non_functional": describes quality attributes (e.g. "API must respond within 2s")
- "constraint": describes a limitation/rule (e.g. "must support only Chrome and Firefox")

Also give a confidence score (0.0 to 1.0) for how clearly this is a requirement.

Return ONLY valid JSON — a list of objects, no extra text, no markdown fences:
[
  {{"text": "<requirement sentence, cleaned up>", "type": "functional", "confidence": 0.95}},
  ...
]

If NO requirements are found, return an empty list: []

TEXT TO ANALYZE:
---
{input_text}
---

JSON OUTPUT:"""


def _call_llm(prompt: str) -> str:
    """Call OpenAI chat completion. Lazy import so app starts without the key."""
    from openai import OpenAI
    from app.config import settings

    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set in your .env file. "
            "Agent 1 (Extractor) needs it to call the LLM."
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


def _parse_json_list(raw: str) -> list:
    """Strip markdown fences if present, then parse JSON."""
    text = raw.strip()
    if text.startswith("```"):
        # remove ```json ... ``` or ``` ... ```
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []


def extractor_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Agent 1.
    Reads state['raw_text'], writes state['extracted_requirements'].
    """
    raw_text = state.get("raw_text", "")
    errors = state.get("errors", [])

    if not raw_text or not raw_text.strip():
        return {
            **state,
            "extracted_requirements": [],
            "status": "extracting",
            "errors": errors + ["extractor_node: empty input text"],
        }

    try:
        prompt = EXTRACTION_PROMPT.format(input_text=raw_text)
        raw_response = _call_llm(prompt)
        parsed = _parse_json_list(raw_response)

        requirements: list[ExtractedRequirement] = []
        for item in parsed:
            text = item.get("text", "").strip()
            if not text:
                continue
            requirements.append({
                "text": text,
                "type": item.get("type", "functional"),
                "confidence": float(item.get("confidence", 0.8)),
            })

        return {
            **state,
            "extracted_requirements": requirements,
            "status": "extracting",
        }

    except Exception as e:
        return {
            **state,
            "extracted_requirements": [],
            "status": "error",
            "errors": errors + [f"extractor_node: {str(e)}"],
        }
