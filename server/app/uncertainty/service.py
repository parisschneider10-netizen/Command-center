"""Uncertainty fallback — halt low-confidence perception before execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.models import UncertaintyReview, UncertaintyStatus
from app.ready_room.service import write_intent_note
from app.services import log_activity


def parse_confidence(meta: dict[str, Any], extracted_text: str = "") -> tuple[float, str | None]:
    """Score 0–1 from vision frontmatter + heuristics."""
    raw = meta.get("confidence_score")
    try:
        score = float(raw) if raw is not None else 0.75
    except (TypeError, ValueError):
        score = 0.75

    reason = meta.get("uncertainty_reason") or meta.get("confidence_note")
    text = (extracted_text or "").strip()
    intent = str(meta.get("intent") or "").strip()

    if not intent or len(intent) < 8:
        score = min(score, 0.5)
        reason = reason or "Intent unclear or missing"
    if len(text) < 80:
        score = min(score, 0.6)
        reason = reason or "Extraction too short"
    if meta.get("illegible") or meta.get("unreadable"):
        score = min(score, 0.3)
        reason = reason or "Marked illegible by vision model"

    return max(0.0, min(1.0, score)), reason


def below_threshold(score: float) -> bool:
    return score < settings.uncertainty_confidence_threshold


async def queue_review(
    db: AsyncSession,
    *,
    source_node: str,
    payload: dict[str, Any],
    confidence_score: float,
    reason: str | None = None,
    vault_path: str | None = None,
) -> UncertaintyReview:
    row = UncertaintyReview(
        source_node=source_node,
        payload_json=json.dumps(payload, default=str),
        confidence_score=confidence_score,
        reason=reason,
        vault_path=vault_path,
        status=UncertaintyStatus.pending,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await log_activity(
        db,
        "uncertainty_queued",
        f"{source_node}: confidence {confidence_score:.2f}",
        {"review_id": row.id, "reason": reason},
    )
    await trigger_n8n(
        "uncertainty-queued",
        {"review_id": row.id, "source": source_node, "confidence": confidence_score},
    )
    return row


async def pending_count(db: AsyncSession) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(UncertaintyReview)
            .where(UncertaintyReview.status == UncertaintyStatus.pending)
        )
        or 0
    )


async def list_reviews(
    db: AsyncSession,
    *,
    status: UncertaintyStatus | None = None,
    limit: int = 50,
) -> list[UncertaintyReview]:
    q = select(UncertaintyReview).order_by(desc(UncertaintyReview.created_at)).limit(limit)
    if status:
        q = q.where(UncertaintyReview.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_review(db: AsyncSession, review_id: int) -> UncertaintyReview | None:
    return await db.get(UncertaintyReview, review_id)


async def resolve_review(
    db: AsyncSession,
    review_id: int,
    *,
    action: str,
    corrected_intent: str | None = None,
    notes: str | None = None,
    mode: str = "live",
) -> dict:
    review = await get_review(db, review_id)
    if not review:
        return {"ok": False, "error": "Review not found"}
    if review.status != UncertaintyStatus.pending:
        return {"ok": False, "error": f"Already {review.status.value}"}

    now = datetime.now(timezone.utc)
    intent_path = None

    if action == "reject":
        review.status = UncertaintyStatus.rejected
        review.commander_resolution = notes or "Rejected by Commander"
    elif action in ("approve", "override"):
        review.status = (
            UncertaintyStatus.overridden if action == "override" else UncertaintyStatus.approved
        )
        review.commander_resolution = notes
        intent_text = (corrected_intent or "").strip()
        if not intent_text:
            payload = json.loads(review.payload_json)
            intent_text = str(payload.get("intent") or payload.get("suggested_intent") or "").strip()
        if intent_text:
            review.resolved_intent = intent_text
            path = write_intent_note(intent_text, mode=mode, auto_execute=True)
            intent_path = str(path)
    else:
        return {"ok": False, "error": "action must be approve, override, or reject"}

    review.resolved_at = now
    await db.commit()
    await log_activity(
        db,
        "uncertainty_resolved",
        f"Review {review_id} → {review.status.value}",
        {"review_id": review_id, "intent_path": intent_path},
    )
    return {
        "ok": True,
        "review_id": review_id,
        "status": review.status.value,
        "intent_path": intent_path,
        "next": "POST /api/ready-room/scan" if intent_path else None,
    }
