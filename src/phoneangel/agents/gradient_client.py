"""DigitalOcean Gradient AI client — wraps the SDK for PhoneAngel agents."""

from __future__ import annotations

import json
import structlog
import httpx

from phoneangel.config import settings

log = structlog.get_logger()

# ── Gradient AI Serverless Inference endpoint ──────────────────────────
GRADIENT_BASE = "https://cluster-api.do-ai.run/v1"


async def gradient_chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 4096,
) -> str:
    """Send a chat completion to Gradient AI serverless inference.

    Uses the OpenAI-compatible /chat/completions endpoint on Gradient.
    """
    model = model or settings.GRADIENT_MODEL

    headers = {
        "Authorization": f"Bearer {settings.DO_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{GRADIENT_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]


async def gradient_agent_chat(
    agent_id: str,
    message: str,
    thread_id: str | None = None,
) -> dict:
    """Send a message to a Gradient AI managed agent.

    Returns both the response text and thread_id for multi-turn conversations.
    """
    headers = {
        "Authorization": f"Bearer {settings.DO_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload: dict = {"message": message}
    if thread_id:
        payload["thread_id"] = thread_id

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"https://cluster-api.do-ai.run/v1/agents/{agent_id}/chat",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "response": data.get("response", ""),
        "thread_id": data.get("thread_id", thread_id),
    }


async def gradient_json_chat(
    messages: list[dict],
    model: str | None = None,
) -> dict:
    """Chat completion that forces JSON output and parses it."""
    raw = await gradient_chat(messages, model=model)

    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning("gradient_json_chat: failed to parse JSON, returning raw", raw=raw[:200])
        return {"raw_response": raw}


async def gradient_agent_endpoint_json_chat(
    endpoint: str,
    api_key: str,
    messages: list[dict],
    temperature: float = 0.4,
    max_tokens: int = 4096,
) -> dict:
    """Call a Gradient agent endpoint (agents.do-ai.run) and parse JSON content.

    The agent is instructed to respond with a JSON object in the message content,
    so we extract the first choice's content and reuse the same cleaning/JSON
    parsing logic as `gradient_json_chat`.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    base = endpoint.rstrip("/")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{base}/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    raw = data["choices"][0]["message"]["content"]

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning(
            "gradient_agent_endpoint_json_chat: failed to parse JSON, returning raw",
            raw=raw[:200],
        )
        return {"raw_response": raw}
