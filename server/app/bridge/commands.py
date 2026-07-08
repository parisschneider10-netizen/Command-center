"""Parse inbound commands from email, webhooks, and bridge API."""

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.n8n import trigger_n8n
from app.models import Decision, TaskPriority, TaskStatus
from app.schemas import TaskCreate
from app.services import create_task, log_activity
from app.vault import write_inbox_note

COMMAND_PREFIXES = ("[BUILD]", "[WILL]", "[COMMAND]", "[NOTE]", "[NUCLEAR]")


def parse_command(subject: str, body: str) -> dict | None:
    """
    Extract command from subject line prefix.
    Examples:
      [BUILD] Portal treasury tab → build task, priority high
      [WILL] Lock KC laundry revenue → will task, priority urgent
      [NOTE] Research Starlink gen 3 → vault dump only
    """
    text = (subject or "").strip()
    upper = text.upper()
    for prefix in COMMAND_PREFIXES:
        if upper.startswith(prefix):
            title = text[len(prefix) :].strip() or "Command from bridge"
            kind = prefix.strip("[]").lower()
            return {
                "kind": kind,
                "title": title,
                "body": (body or "").strip(),
            }
    return None


async def execute_command(
    db: AsyncSession,
    *,
    kind: str,
    title: str,
    body: str = "",
    source: str = "bridge",
    metadata: dict | None = None,
) -> dict:
    """Route a parsed command to tasks, vault, or nuclear queue."""
    meta = metadata or {}

    if kind == "note":
        path = write_inbox_note(title, body or title, source=source)
        await log_activity(db, "bridge_note", f"Vault note: {title}", meta)
        return {"ok": True, "action": "vault_note", "vault_file": path.name}

    if kind == "nuclear":
        decision = Decision(
            title=title,
            context=body or title,
            recommendation="Commander decision required — inbound via communication bridge.",
            status="pending",
        )
        db.add(decision)
        await db.commit()
        await db.refresh(decision)
        await log_activity(db, "bridge_nuclear", f"Nuclear queued: {title}", meta)
        return {"ok": True, "action": "nuclear_queue", "decision_id": decision.id}

    priority = TaskPriority.normal
    will_priority = 5
    open_for_agents = True

    if kind == "build":
        priority = TaskPriority.high
        will_priority = 8
    elif kind == "will":
        priority = TaskPriority.urgent
        will_priority = 9
    elif kind == "command":
        priority = TaskPriority.normal
        will_priority = 6

    task = await create_task(
        db,
        TaskCreate(
            title=title,
            description=body or None,
            priority=priority,
            source=source,
            will_priority=will_priority,
            open_for_agents=open_for_agents,
        ),
    )
    await trigger_n8n(
        "task-created",
        {"task_id": task.id, "title": task.title, "priority": task.priority.value, "source": source},
    )
    await trigger_n8n(
        "agent-queue",
        {"task_id": task.id, "title": task.title, "will_priority": task.will_priority, "bridge": True},
    )
    if kind in ("build", "will"):
        await trigger_n8n(
            "bridge-build",
            {"task_id": task.id, "title": task.title, "kind": kind, "github_hint": "File matching GitHub Issue for @cursor"},
        )

    await log_activity(
        db,
        "bridge_command",
        f"[{kind.upper()}] {title}",
        {"task_id": task.id, **meta},
    )
    return {
        "ok": True,
        "action": "task_created",
        "task_id": task.id,
        "kind": kind,
        "will_priority": will_priority,
        "github_next_step": "Open GitHub Issue with @cursor and reference this task_id for Cloud Agent build",
    }


async def process_email_commands(db: AsyncSession, *, allowed_senders: list[str]) -> list[dict]:
    """Scan inbox for [BUILD]/[COMMAND] emails and convert to tasks."""
    from sqlalchemy import select

    from app.models import EmailMessage

    allowed = {s.lower() for s in allowed_senders if s}
    result = await db.execute(
        select(EmailMessage).where(EmailMessage.status == "received").order_by(EmailMessage.received_at)
    )
    processed = []
    for msg in result.scalars().all():
        parsed = parse_command(msg.subject, msg.body_text or "")
        if not parsed:
            continue
        if allowed:
            from_addr = msg.from_addr.lower()
            if not any(a in from_addr for a in allowed):
                msg.status = "ignored_sender"
                continue
        outcome = await execute_command(
            db,
            kind=parsed["kind"],
            title=parsed["title"],
            body=parsed["body"],
            source="email_bridge",
            metadata={"email_id": msg.id, "from": msg.from_addr},
        )
        msg.status = "command_processed"
        msg.agent_summary = f"Bridge: {outcome.get('action')} — task {outcome.get('task_id', 'n/a')}"
        processed.append({**outcome, "email_id": msg.id, "subject": msg.subject})
    if processed:
        await db.commit()
    return processed


def normalize_github_issue_body(body: str) -> dict | None:
    """If issue body starts with @cursor, treat as build command."""
    if not body:
        return None
    if re.search(r"@cursor\b", body, re.I):
        lines = body.strip().splitlines()
        title_line = next((ln for ln in lines if ln.strip() and not ln.strip().startswith("@")), body[:200])
        return {"kind": "build", "title": title_line.strip()[:255], "body": body}
    return None
