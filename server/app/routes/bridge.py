from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.bridge.commands import execute_command, normalize_github_issue_body, process_email_commands
from app.comms.email import comms_configured, sync_inbox
from app.config import settings
from app.database import get_db
from app.doctrine import doctrine_snapshot
from app.integrations.telegram_bridge import telegram_configured

router = APIRouter(prefix="/api/bridge", tags=["communication-bridge"])


class BridgeCommand(BaseModel):
    kind: str = Field(description="build | will | command | note | nuclear")
    title: str
    body: str = ""
    source: str = "api"


class WebhookPayload(BaseModel):
    title: str
    body: str = ""
    kind: str = "build"
    source: str = "webhook"


def _allowed_senders() -> list[str]:
    raw = settings.bridge_allowed_senders
    return [s.strip() for s in raw.split(",") if s.strip()]


def _verify_bridge_secret(x_bridge_secret: str | None) -> None:
    if not settings.bridge_webhook_secret:
        return
    if x_bridge_secret != settings.bridge_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid bridge secret")


@router.get("/status")
async def bridge_status(_: str = Depends(get_current_user)) -> dict:
    """Which communication channels are live right now."""
    senders = _allowed_senders()
    return {
        "doctrine": doctrine_snapshot(settings.vault_path),
        "channels": {
            "github_issues": {
                "live": True,
                "primary": True,
                "how": "GitHub Issue → @cursor in body → Cloud Agent builds PR",
                "mobile": "GitHub app on phone",
                "doc": "docs/GITHUB_COMMAND.md",
            },
            "voice_sara": {
                "live": bool(settings.public_base_url),
                "how": "Call Vapi number → SARA creates tasks, vault notes, briefings",
                "doc": "docs/VAPI_SETUP.md",
            },
            "command_deck_portal": {
                "live": bool(settings.public_base_url),
                "how": "HTTPS portal — tasks, empire tab, treasury",
            },
            "email_commands": {
                "live": comms_configured(),
                "how": "Email [BUILD] Subject to commander@yourdomain.com (NOT Gmail→Cursor)",
                "allowed_senders": senders or ["configure BRIDGE_ALLOWED_SENDERS"],
                "prefixes": ["[BUILD]", "[WILL]", "[COMMAND]", "[NOTE]", "[NUCLEAR]"],
            },
            "bridge_webhook": {
                "live": bool(settings.bridge_webhook_secret),
                "how": "POST /api/bridge/webhook with X-Bridge-Secret header (n8n, Zapier)",
            },
            "ready_room_chat": {
                "live": True,
                "primary": True,
                "how": "Text + file upload like Cursor — POST /api/ready-room/chat and /chat/upload",
                "mobile": "Telegram bot (optional) or portal",
                "doc": "vault/commander/ready-room-chat-manual.md",
                "vault": "vault/ready-room/chat/",
            },
            "telegram": {
                "live": telegram_configured(),
                "how": "Your bot → POST /api/telegram/webhook → same Ready Room pipeline",
                "doc": "vault/commander/ready-room-chat-manual.md",
                "sovereign": "Transport only — token on VPS, messages copied to vault",
            },
        },
        "gmail_answer": {
            "connect_gmail_to_cursor": False,
            "instead": [
                "Forward Gmail → commander@yourdomain.com → comms sync → [BUILD] commands",
                "OR GitHub email-to-issue → @cursor in issue",
                "OR call SARA on Vapi",
                "OR GitHub mobile app → new Issue → @cursor",
            ],
        },
        "before_command_deck_online": [
            "1. GitHub Issue @cursor (works from phone, no VPS needed)",
            "2. GitHub Secrets once → Actions Deploy + Wire SARA (no SSH, no dashboards)",
            "3. Call SARA once machine-wire completes",
        ],
        "money_play_after_deploy": [
            "Sovereign Stay presale → POST /api/sovereign-stay/presale (sandbox instant treasury)",
            "40 cities × 3 units — funded sandbox grid",
            "Ground force deploy → /api/ground-force/deploy",
            "Treasury ammo → sovereign acquisitions auto-fund on instant clear",
        ],
        "commander_loop": {
            "at_work_no_vps": "GitHub mobile → Issue → @cursor (works now)",
            "after_vps": "Ready Room chat / Telegram / SARA voice / portal / GitHub Issues",
            "not_gmail_to_cursor": "Forward to sovereign mail OR GitHub email-to-issue",
        },
    }


@router.post("/command")
async def bridge_command(
    body: BridgeCommand,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Unified command ingress from portal or authenticated clients."""
    kind = body.kind.lower()
    if kind not in ("build", "will", "command", "note", "nuclear"):
        raise HTTPException(status_code=400, detail="kind must be build|will|command|note|nuclear")
    return await execute_command(
        db,
        kind=kind,
        title=body.title,
        body=body.body,
        source=body.source,
    )


@router.post("/webhook")
async def bridge_webhook(
    body: WebhookPayload,
    db: AsyncSession = Depends(get_db),
    x_bridge_secret: str | None = Header(default=None),
) -> dict:
    """Public webhook for n8n/Zapier — requires X-Bridge-Secret if configured."""
    _verify_bridge_secret(x_bridge_secret)
    kind = body.kind.lower()
    if kind not in ("build", "will", "command", "note", "nuclear"):
        raise HTTPException(status_code=400, detail="Invalid kind")
    return await execute_command(
        db,
        kind=kind,
        title=body.title,
        body=body.body,
        source=body.source,
    )


@router.post("/github")
async def bridge_github_issue(
    body: dict,
    db: AsyncSession = Depends(get_db),
    x_bridge_secret: str | None = Header(default=None),
) -> dict:
    """
    Ingest GitHub issue payload (n8n GitHub trigger).
    Body: { "title": "...", "body": "...", "number": 42 }
  """
    _verify_bridge_secret(x_bridge_secret)
    issue_body = body.get("body") or ""
    parsed = normalize_github_issue_body(issue_body)
    if not parsed:
        return {"ok": False, "skipped": True, "reason": "No @cursor in issue body"}
    title = body.get("title") or parsed["title"]
    return await execute_command(
        db,
        kind=parsed["kind"],
        title=title,
        body=issue_body,
        source="github_bridge",
        metadata={"issue_number": body.get("number")},
    )


@router.post("/email/sync-commands")
async def bridge_email_sync_commands(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Pull sovereign mail inbox + convert [BUILD]/[COMMAND] emails to tasks.
    Configure comms IMAP + BRIDGE_ALLOWED_SENDERS (your personal email).
    """
    if not comms_configured():
        raise HTTPException(
            status_code=503,
            detail="Comms not configured — set COMMS_IMAP_* in .env (sovereign mail, not Gmail API)",
        )
    synced = await sync_inbox(db)
    processed = await process_email_commands(db, allowed_senders=_allowed_senders())
    return {"synced_emails": synced, "commands_processed": len(processed), "results": processed}
