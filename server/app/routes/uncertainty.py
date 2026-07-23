"""Uncertainty fallback queue API."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import UncertaintyStatus
from app.schemas_uncertainty import UncertaintyResolveIn, UncertaintyReviewOut
from app.uncertainty.service import (
    get_review,
    list_reviews,
    pending_count,
    resolve_review,
)

router = APIRouter(prefix="/api/uncertainty", tags=["uncertainty"])


@router.get("/status")
async def uncertainty_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    pending = await pending_count(db)
    return {
        "ok": True,
        "pending": pending,
        "confidence_threshold": settings.uncertainty_confidence_threshold,
        "manual": "Review low-confidence vision/classifier output before live execution.",
    }


@router.get("/reviews", response_model=list[UncertaintyReviewOut])
async def get_reviews(
    status: str | None = "pending",
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[UncertaintyReviewOut]:
    st = UncertaintyStatus(status) if status else None
    rows = await list_reviews(db, status=st)
    return [UncertaintyReviewOut.model_validate(r) for r in rows]


@router.get("/reviews/{review_id}")
async def get_review_detail(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    row = await get_review(db, review_id)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    payload = json.loads(row.payload_json)
    return {
        "review": UncertaintyReviewOut.model_validate(row),
        "payload": payload,
    }


@router.post("/reviews/{review_id}/resolve")
async def post_resolve(
    review_id: int,
    body: UncertaintyResolveIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    result = await resolve_review(
        db,
        review_id,
        action=body.action,
        corrected_intent=body.corrected_intent,
        notes=body.notes,
        mode=body.mode,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "resolve failed"))
    return result
