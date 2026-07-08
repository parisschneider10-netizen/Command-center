"""RentAHuman ground force — zero upfront, pay on completion."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.n8n import trigger_n8n
from app.integrations.rentahuman import create_bounty
from app.models import GroundForceMission
from app.services import log_activity

MISSION_TEMPLATES = {
    "host_visit": {
        "title": "KC Host Visit — {neighborhood}",
        "description": (
            "Visit STR host at {address}. Pitch complimentary laundry amenity. "
            "Get signed one-pager or QR placement agreement. Photo proof required. "
            "PAY ON COMPLETION — host signup or signed sheet."
        ),
        "default_pay_cents": 3500,
        "tags": ["ground-force", "host-visit", "kcmo"],
    },
    "sticker_post": {
        "title": "KC Sticker Drop — {neighborhood}",
        "description": (
            "Place QR stickers at approved host properties ONLY (list provided). "
            "Guest laundry pickup QR. Photo each placement. "
            "PAY ON COMPLETION — photo proof uploaded."
        ),
        "default_pay_cents": 2000,
        "tags": ["ground-force", "stickers", "kcmo"],
    },
    "guerrilla_guest": {
        "title": "KC Guest Outreach — {neighborhood}",
        "description": (
            "High-traffic World Cup / STR corridor. Hand guests QR cards for laundry pickup. "
            "Friendly, brief pitch. 20+ cards distributed. "
            "PAY ON COMPLETION — count + location report."
        ),
        "default_pay_cents": 2500,
        "tags": ["ground-force", "guerrilla", "kcmo"],
    },
}


async def deploy_mission(
    db: AsyncSession,
    *,
    mission_type: str,
    neighborhood: str,
    target_address: str | None = None,
    host_id: int | None = None,
    pay_cents: int | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Game theory: worker paid ONLY on verified completion.
    Empire posts RentAHuman bounty — zero float out until host revenue clears hold.
    """
    template = MISSION_TEMPLATES.get(mission_type)
    if not template:
        return {"ok": False, "error": f"Unknown mission type: {mission_type}"}

    pay = pay_cents or template["default_pay_cents"]
    title = template["title"].format(neighborhood=neighborhood)
    description = template["description"].format(
        neighborhood=neighborhood,
        address=target_address or "see briefing",
    )

    mission = GroundForceMission(
        mission_type=mission_type,
        title=title,
        neighborhood=neighborhood,
        target_address=target_address,
        pay_on_completion_cents=pay,
        host_id=host_id,
        status="bounty_posted",
    )
    db.add(mission)
    await db.commit()
    await db.refresh(mission)

    bounty = await create_bounty(
        title=title,
        description=description + f"\n\nMission ID: {mission.id}. Pay: ${pay/100:.2f} on verified completion.",
        compensation=pay / 100,
        location=f"Kansas City, MO — {neighborhood}",
        tags=template["tags"],
        dry_run=dry_run,
    )

    if bounty.get("ok") and bounty.get("data"):
        mission.rentahuman_bounty_id = str(bounty["data"].get("id", ""))
        await db.commit()

    await log_activity(
        db,
        "ground_force_deploy",
        f"{mission_type} → {neighborhood}",
        {"mission_id": mission.id, "pay_cents": pay, "dry_run": dry_run},
    )
    await trigger_n8n(
        "ground-force-deploy",
        {
            "mission_id": mission.id,
            "type": mission_type,
            "neighborhood": neighborhood,
            "pay_cents": pay,
            "bounty": bounty,
        },
    )

    return {
        "ok": True,
        "mission_id": mission.id,
        "mission_type": mission_type,
        "pay_on_completion_cents": pay,
        "rentahuman": bounty,
        "game_theory": "Worker paid on completion. Host pays upfront. 48h hold before disbursement.",
    }


async def complete_mission(
    db: AsyncSession,
    mission_id: int,
    proof_notes: str,
    worker_ref: str,
    ledger_id: int | None = None,
) -> dict:
    from datetime import datetime, timezone

    from app.treasury.float import payout_worker, release_cleared_holds

    mission = await db.get(GroundForceMission, mission_id)
    if not mission:
        return {"ok": False, "error": "Mission not found"}

    await release_cleared_holds(db)
    mission.status = "completed"
    mission.proof_notes = proof_notes
    mission.completed_at = datetime.now(timezone.utc)
    await db.commit()

    try:
        payout = await payout_worker(
            db,
            amount_cents=mission.pay_on_completion_cents,
            mission_id=mission_id,
            worker_ref=worker_ref,
            from_ledger_id=ledger_id,
        )
        return {"ok": True, "mission_id": mission_id, "payout_id": payout.id}
    except ValueError as exc:
        mission.status = "completed_pending_payout"
        await db.commit()
        return {
            "ok": True,
            "mission_id": mission_id,
            "payout_pending": True,
            "reason": str(exc),
        }
