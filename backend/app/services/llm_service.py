"""
Shared LLM client used by all 4 agent nodes (Extractor, Coverage, Risk,
PR Reviewer).

Two providers, switched by LLM_PROVIDER in .env:

  LLM_PROVIDER=openai  (default) — calls OpenAI GPT-4o-mini, needs
                         OPENAI_API_KEY, costs money, has rate limits.

  LLM_PROVIDER=ollama  — calls a locally running Ollama model
                         (e.g. `ollama pull llama3.1` then
                         `ollama serve`). No API key, no cost, no
                         rate limits, runs fully offline.

Every agent node should call `call_llm(prompt)` from here instead of
building its own OpenAI client — this is the single place that knows
which provider is active.
"""
import httpx
from app.config import settings


def call_llm(prompt: str, temperature: float = 0.1) -> str:
    """
    Send `prompt` to whichever LLM provider is configured and return the
    raw text response. Raises RuntimeError with a clear message if the
    active provider isn't configured correctly.
    """
    provider = (settings.LLM_PROVIDER or "openai").lower().strip()

    if provider == "ollama":
        return _call_ollama(prompt, temperature)
    return _call_openai(prompt, temperature)


def _call_openai(prompt: str, temperature: float) -> str:
    from openai import OpenAI

    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "LLM_PROVIDER=openai but OPENAI_API_KEY is not set in your .env file. "
            "Either add a key, or set LLM_PROVIDER=ollama to run locally instead."
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _call_ollama(prompt: str, temperature: float) -> str:
    """
    Calls a locally running Ollama server's /api/chat endpoint.
    Requires Ollama installed and running (`ollama serve`) with the
    configured model pulled (`ollama pull llama3.1` or similar).
    """
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        resp = httpx.post(url, json=payload, timeout=120.0)
        resp.raise_for_status()
    except httpx.ConnectError as e:
        raise RuntimeError(
            f"Could not reach Ollama at {settings.OLLAMA_BASE_URL}. "
            "Is it installed and running? Start it with `ollama serve`, "
            f"and make sure the model is pulled: `ollama pull {settings.OLLAMA_MODEL}`."
        ) from e
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Ollama returned an error ({e.response.status_code}). "
            f"Is the model pulled? Try: `ollama pull {settings.OLLAMA_MODEL}`."
        ) from e

    data = resp.json()
    content = data.get("message", {}).get("content", "")
    return content.strip()
