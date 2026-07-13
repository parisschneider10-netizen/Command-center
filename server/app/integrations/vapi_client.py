"""Vapi REST API — wire SARA without dashboard clicks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from app.config import settings

VAPI_BASE = "https://api.vapi.ai"


def _headers() -> dict[str, str]:
    if not settings.vapi_api_key:
        raise ValueError("VAPI_API_KEY not configured")
    return {
        "Authorization": f"Bearer {settings.vapi_api_key}",
        "Content-Type": "application/json",
    }


def _template_path() -> Path:
    candidates = [
        Path(settings.vault_path) / ".." / "docs" / "vapi-assistant.json",
        Path("/app/docs/vapi-assistant.json"),
        Path(__file__).resolve().parents[3] / "docs" / "vapi-assistant.json",
    ]
    for path in candidates:
        resolved = path.resolve()
        if resolved.exists():
            return resolved
    raise FileNotFoundError("docs/vapi-assistant.json not found")


def _substitute_base(obj: Any, base: str) -> Any:
    if isinstance(obj, str):
        return obj.replace("https://YOUR-VPS-DOMAIN.com", base.rstrip("/"))
    if isinstance(obj, list):
        return [_substitute_base(item, base) for item in obj]
    if isinstance(obj, dict):
        return {k: _substitute_base(v, base) for k, v in obj.items()}
    return obj


def build_assistant_payload(https_base: str, *, include_tools: bool = True) -> dict[str, Any]:
    """Map repo template → Vapi PATCH body (tools live under model, not assistant root)."""
    raw = json.loads(_template_path().read_text())
    data = _substitute_base(raw, https_base.rstrip("/"))
    tools = []
    for tool in data.get("tools", []):
        fn = tool.get("function", {})
        tools.append(
            {
                "type": "function",
                "async": False,
                "function": {
                    "name": fn.get("name"),
                    "description": fn.get("description", ""),
                    "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
                },
                "server": tool.get("server"),
            }
        )
    model: dict[str, Any] = {
        "provider": data.get("model", {}).get("provider", "openai"),
        "model": data.get("model", {}).get("model", "gpt-4o"),
        "temperature": data.get("model", {}).get("temperature", 0.3),
        "messages": [
            {"role": "system", "content": data.get("systemPrompt", "You are SARA.")},
        ],
    }
    if include_tools and tools:
        model["tools"] = tools

    payload: dict[str, Any] = {
        "name": data.get("name", "SARA — Voice OS"),
        "firstMessage": data.get("firstMessage"),
        "endCallMessage": data.get("endCallMessage"),
        "silenceTimeoutSeconds": data.get("silenceTimeoutSeconds", 30),
        "maxDurationSeconds": data.get("maxDurationSeconds", 600),
        "server": {"url": f"{https_base.rstrip('/')}/vapi/webhook"},
        "serverMessages": data.get("serverMessages", ["end-of-call-report", "status-update"]),
        "model": model,
    }
    voice = data.get("voice")
    voice_id = settings.sara_voice_id or (voice or {}).get("voiceId", "")
    if voice and voice_id and voice_id not in ("YOUR_VOICE_ID", ""):
        payload["voice"] = {**voice, "voiceId": voice_id}
    return payload


async def get_assistant(assistant_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{VAPI_BASE}/assistant/{assistant_id}",
            headers=_headers(),
        )
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json()
            except Exception:
                pass
            raise ValueError(f"Vapi GET assistant failed ({response.status_code}): {detail}")
        return response.json()


def find_replit_urls(obj: Any) -> list[str]:
    """Recursively find replit.dev / replit.app URLs in Vapi assistant JSON."""
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            lower = value.lower()
            if "replit.dev" in lower or "replit.app" in lower:
                found.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(obj)
    return sorted(set(found))


async def list_phone_numbers() -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{VAPI_BASE}/phone-number", headers=_headers())
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json()
            except Exception:
                pass
            raise ValueError(f"Vapi list phone numbers failed ({response.status_code}): {detail}")
        body = response.json()
        if isinstance(body, list):
            return body
        return body.get("data", body.get("phoneNumbers", []))


def format_phone_number(row: dict) -> str | None:
    """Best-effort E.164 / display number from Vapi phone object."""
    for key in ("number", "phoneNumber", "twilioPhoneNumber", "telnyxPhoneNumber"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


async def resolve_primary_phone() -> dict | None:
    """First Vapi number on account — used when VAPI_PHONE_NUMBER_ID unset."""
    numbers = await list_phone_numbers()
    if not numbers:
        return None
    row = numbers[0]
    return {
        "id": row.get("id", ""),
        "number": format_phone_number(row),
        "name": row.get("name"),
        "assistant_id": row.get("assistantId"),
    }


async def list_assistants() -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{VAPI_BASE}/assistant", headers=_headers())
        response.raise_for_status()
        body = response.json()
        if isinstance(body, list):
            return body
        return body.get("data", body.get("assistants", []))


async def update_assistant(assistant_id: str, payload: dict[str, Any]) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.patch(
            f"{VAPI_BASE}/assistant/{assistant_id}",
            headers=_headers(),
            json=payload,
        )
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json()
            except Exception:
                pass
            raise ValueError(f"Vapi PATCH assistant failed ({response.status_code}): {detail}")
        return response.json()


async def update_phone_number(phone_id: str, assistant_id: str, server_url: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            f"{VAPI_BASE}/phone-number/{phone_id}",
            headers=_headers(),
            json={
                "assistantId": assistant_id,
                "server": {"url": f"{server_url.rstrip('/')}/vapi/webhook"},
            },
        )
        response.raise_for_status()
        return response.json()


async def wire_assistant(https_base: str) -> dict:
    """PATCH assistant + optional phone — full API wire."""
    assistant_id = settings.vapi_assistant_id.strip()
    if not assistant_id:
        assistants = await list_assistants()
        if not assistants:
            raise ValueError("No Vapi assistants found — set VAPI_ASSISTANT_ID in .env")
        assistant_id = assistants[0].get("id", "")
        if not assistant_id:
            raise ValueError("Could not resolve assistant id from Vapi")

    tools_wired = True
    try:
        updated = await update_assistant(
            assistant_id, build_assistant_payload(https_base, include_tools=True)
        )
    except ValueError as exc:
        # Vapi PATCH rejects assistant-root tools; if model.tools also fails, wire webhook only.
        if "tools" not in str(exc).lower():
            raise
        tools_wired = False
        updated = await update_assistant(
            assistant_id, build_assistant_payload(https_base, include_tools=False)
        )

    phone_result = None
    phone_id = settings.vapi_phone_number_id.strip()
    if not phone_id:
        primary = await resolve_primary_phone()
        if primary and primary.get("id"):
            phone_id = primary["id"]
    if phone_id:
        phone_result = await update_phone_number(
            phone_id,
            assistant_id,
            https_base,
        )

    primary_phone = await resolve_primary_phone()

    return {
        "ok": True,
        "assistant_id": assistant_id,
        "https_base": https_base,
        "webhook_url": f"{https_base.rstrip('/')}/vapi/webhook",
        "assistant_name": updated.get("name"),
        "phone_updated": phone_result is not None,
        "phone_number": (primary_phone or {}).get("number"),
        "phone_number_id": (primary_phone or {}).get("id") or phone_id or None,
        "tools_wired": tools_wired,
    }
