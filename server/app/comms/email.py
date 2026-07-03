"""Sovereign comms — IMAP/SMTP inbox for agents (Gmail replacement)."""

import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import EmailMessage
from app.services import log_activity


def comms_configured() -> bool:
    return bool(settings.comms_imap_host and settings.comms_imap_user)


def sync_inbox_blocking(db_messages: list[dict]) -> list[dict]:
    """Sync inbox via IMAP (blocking — run in thread pool in production)."""
    if not comms_configured():
        return []

    fetched = []
    mail = imaplib.IMAP4_SSL(settings.comms_imap_host, settings.comms_imap_port)
    mail.login(settings.comms_imap_user, settings.comms_imap_password)
    mail.select("INBOX")

    status, data = mail.search(None, "UNSEEN")
    if status != "OK":
        mail.logout()
        return []

    existing_ids = {m["message_id"] for m in db_messages if m.get("message_id")}

    for num in data[0].split()[-50:]:
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        msg_id = msg.get("Message-ID", "")
        if msg_id in existing_ids:
            continue

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(errors="replace")
                    break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(errors="replace")

        date_hdr = msg.get("Date")
        received = parsedate_to_datetime(date_hdr) if date_hdr else None

        fetched.append(
            {
                "message_id": msg_id,
                "from_addr": msg.get("From", ""),
                "to_addr": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "body_text": body[:50000],
                "received_at": received,
            }
        )

    mail.logout()
    return fetched


async def sync_inbox(db: AsyncSession) -> int:
    result = await db.execute(
        select(EmailMessage.message_id).where(EmailMessage.message_id.isnot(None))
    )
    existing = [{"message_id": r} for r in result.scalars().all()]

    import asyncio

    new_messages = await asyncio.to_thread(sync_inbox_blocking, existing)
    count = 0
    for m in new_messages:
        entry = EmailMessage(
            message_id=m["message_id"],
            direction="inbound",
            from_addr=m["from_addr"],
            to_addr=m["to_addr"],
            subject=m["subject"],
            body_text=m["body_text"],
            status="received",
        )
        db.add(entry)
        count += 1

    if count:
        await db.commit()
        await log_activity(db, "comms_sync", f"Synced {count} new emails")
    return count


async def list_inbox(db: AsyncSession, limit: int = 50) -> list[EmailMessage]:
    result = await db.execute(
        select(EmailMessage).order_by(desc(EmailMessage.received_at)).limit(limit)
    )
    return list(result.scalars().all())


def send_email_blocking(to: str, subject: str, body: str) -> dict:
    if not settings.comms_smtp_host:
        return {"sent": False, "error": "SMTP not configured"}

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{settings.comms_from_name} <{settings.comms_smtp_user}>"
    msg["To"] = to

    with smtplib.SMTP(settings.comms_smtp_host, settings.comms_smtp_port) as server:
        server.starttls()
        server.login(settings.comms_smtp_user, settings.comms_smtp_password)
        server.send_message(msg)
    return {"sent": True, "to": to}


async def send_email(db: AsyncSession, message_id: int) -> dict:
    msg = await db.get(EmailMessage, message_id)
    if not msg or not msg.draft_reply:
        return {"sent": False, "error": "No draft to send"}

    if msg.nuclear_flag and not settings.comms_auto_send_routine:
        return {"sent": False, "error": "Nuclear flag — Commander approval required"}

    import asyncio

    result = await asyncio.to_thread(
        send_email_blocking,
        msg.from_addr,
        f"Re: {msg.subject}",
        msg.draft_reply,
    )
    if result.get("sent"):
        msg.status = "sent"
        msg.direction = "outbound"
        await db.commit()
        await log_activity(db, "comms_sent", f"Sent reply: {msg.subject}")
    return result
