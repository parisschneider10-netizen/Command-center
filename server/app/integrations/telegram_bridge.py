"""Sovereign Telegram bridge — chat + file upload to Ready Room on YOUR VPS."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

TELEGRAM_API = "https://api.telegram.org"


def commander_chat_ids() -> set[int]:
    raw = settings.telegram_commander_chat_ids.strip()
    if not raw:
        return set()
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


def telegram_configured() -> bool:
    return bool(settings.telegram_bot_token)


def _auth_chat(chat_id: int) -> bool:
    allowed = commander_chat_ids()
    if not allowed:
        return True  # open until Commander sets TELEGRAM_COMMANDER_CHAT_IDS
    return chat_id in allowed


async def telegram_api(method: str, payload: dict | None = None) -> dict:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")
    url = f"{TELEGRAM_API}/bot{settings.telegram_bot_token}/{method}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload or {})
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            raise ValueError(f"Telegram API error: {body}")
        return body.get("result", body)


async def send_message(chat_id: int, text: str) -> dict:
    return await telegram_api(
        "sendMessage",
        {"chat_id": chat_id, "text": text[:4000]},
    )


async def download_largest_photo(file_id: str) -> tuple[bytes, str]:
    meta = await telegram_api("getFile", {"file_id": file_id})
    file_path = meta.get("file_path", "")
    url = f"{TELEGRAM_API}/file/bot{settings.telegram_bot_token}/{file_path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        name = file_path.split("/")[-1] if file_path else "photo.jpg"
        return response.content, name


async def handle_telegram_update(update: dict[str, Any], db) -> dict:
    """Route Telegram message → Ready Room chat (text, photo, scan)."""
    from app.ready_room.chat import handle_chat_message, save_chat_attachment

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True, "ignored": "no message"}

    chat = message.get("chat", {})
    chat_id = int(chat.get("id", 0))
    if not _auth_chat(chat_id):
        await send_message(chat_id, "Unauthorized. Set TELEGRAM_COMMANDER_CHAT_IDS on VPS.")
        return {"ok": False, "error": "unauthorized"}

    text = (message.get("text") or message.get("caption") or "").strip()

    if message.get("photo"):
        photos = message["photo"]
        file_id = photos[-1]["file_id"]
        data, name = await download_largest_photo(file_id)
        mime = "image/jpeg"
        result = await save_chat_attachment(
            db,
            data,
            name,
            mime,
            source="telegram",
            caption=text,
            auto_scan=True,
        )
        await send_message(
            chat_id,
            f"Ready Room: file ingested.\n"
            f"Intent: {result.get('intent') or '(see extracted note)'}\n"
            f"Say 'scan' anytime to re-run queue.",
        )
        return {"ok": True, "telegram": True, **result}

    if not text:
        await send_message(
            chat_id,
            "Send text intent, photo of handwritten note, or: scan / drill / launch …",
        )
        return {"ok": True, "hint": True}

    result = await handle_chat_message(
        db,
        text,
        source="telegram",
        auto_scan=text.lower().strip() not in ("scan", "scan ready room"),
    )

    if result.get("action") == "scan":
        await send_message(
            chat_id,
            f"Scanned. OK: {result.get('ok', 0)}/{result.get('scanned', 0)} intents.",
        )
    elif result.get("action") == "intent":
        await send_message(
            chat_id,
            f"Intent queued ({result.get('mode')}).\n{result.get('path')}\nHive executing.",
        )
    else:
        await send_message(chat_id, f"Done: {result.get('action')}")

    return {"ok": True, "telegram": True, **result}
