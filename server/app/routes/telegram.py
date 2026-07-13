"""Telegram webhook — sovereign chat bridge to Ready Room."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import settings
from app.database import get_db
from app.integrations.telegram_bridge import handle_telegram_update, telegram_configured
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/telegram", tags=["telegram-bridge"])


@router.get("/status")
async def telegram_status() -> dict:
    return {
        "configured": telegram_configured(),
        "webhook_path": "/api/telegram/webhook",
        "sovereign_note": (
            "Telegram is transport only — bot token on YOUR VPS, "
            "messages land in Ready Room, not Big Tech dashboards."
        ),
        "setup": "vault/commander/ready-room-chat-manual.md",
    }


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    """
    Telegram Bot API webhook → Ready Room.
    Set webhook to: https://YOUR_DOMAIN/api/telegram/webhook
    """
    if not telegram_configured():
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN not configured")

    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid telegram webhook secret")

    update = await request.json()
    return await handle_telegram_update(update, db)
