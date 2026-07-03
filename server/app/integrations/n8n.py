"""n8n webhook integration."""

import httpx

from app.config import settings


async def trigger_n8n(event: str, payload: dict) -> dict:
    """Fire an n8n webhook. Returns result or error dict."""
    if not settings.n8n_webhook_base_url:
        return {"triggered": False, "reason": "N8N_WEBHOOK_BASE_URL not configured"}

    url = f"{settings.n8n_webhook_base_url.rstrip('/')}/{event}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            try:
                body = response.json()
            except Exception:
                body = {"status": response.status_code, "text": response.text[:200]}
            return {"triggered": True, "url": url, "response": body}
    except Exception as exc:
        return {"triggered": False, "url": url, "error": str(exc)}
