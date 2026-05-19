import json
import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_SYSTEM_TEMPLATE = """\
Business assistant. Answer from the KB below. KB may include a DB schema — use exact table/column names from it.
If the answer needs live DB records, reply ONLY with this JSON (nothing else):
{{"needs_data":true,"description":"<why>","table":"<table>","fields_needed":["col1","col2"],"filters":{{"col":"val"}}}}
Never invent records or numbers. Plain text answers only.

KB:
{kb}"""


async def ask_llm(messages: list[dict], knowledge_base: str) -> str:
    system_content = _SYSTEM_TEMPLATE.format(kb=knowledge_base or "(No knowledge base loaded)")
    payload = {
        "models": settings.models_list,
        "route": "fallback",
        "messages": [{"role": "system", "content": system_content}, *messages],
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://chatbot.local",
        "X-Title": "Business Chatbot",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(OPENROUTER_URL, json=payload, headers=headers)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            # Try to surface OpenRouter's own error message
            try:
                detail = e.response.json().get("error", {}).get("message", str(e))
            except Exception:
                detail = str(e)
            logger.error(f"OpenRouter {status}: {detail}")
            if status == 401:
                raise HTTPException(502, f"OpenRouter auth failed — check OPENROUTER_API_KEY. Detail: {detail}")
            if status == 404:
                raise HTTPException(502, f"No available model found on OpenRouter. "
                                        f"Check OPENROUTER_MODELS in .env. Detail: {detail}")
            if status == 429:
                raise HTTPException(429, f"Model provider is overloaded — retry in a moment. Detail: {detail}")
            raise HTTPException(502, f"OpenRouter error {status}: {detail}")
        except httpx.TimeoutException:
            raise HTTPException(504, "OpenRouter request timed out — try again")
        body = r.json()
        # OpenRouter sometimes returns 200 with an error body instead of a non-2xx status
        if "error" in body:
            err = body["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            logger.error(f"OpenRouter 200-wrapped error: {msg}")
            raise HTTPException(502, f"OpenRouter returned an error: {msg}")
        if "choices" not in body or not body["choices"]:
            logger.error(f"OpenRouter unexpected response body: {body}")
            raise HTTPException(502, f"OpenRouter returned an unexpected response. Full body: {body}")
        return body["choices"][0]["message"]["content"].strip()


def parse_llm_response(content: str) -> tuple[bool, dict | str]:
    """Return (needs_data, payload).

    payload is a dict when needs_data is True, otherwise the plain-text answer string.
    """
    stripped = content.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict) and parsed.get("needs_data") is True:
                return True, parsed
        except json.JSONDecodeError:
            pass
    return False, content
