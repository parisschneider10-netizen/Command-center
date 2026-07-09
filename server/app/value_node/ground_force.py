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
    "basket_shop": {
        "title": "KC Welcome Basket — Shop run",
        "description": (
            "Shop ONLY from agent-locked spec list (Costco/Sams). Receipt photo required. "
            "Budget ~$16 supplies. Deliver items to assembler or meet point. "
            "PAY ON COMPLETION — receipt + bag photo."
        ),
        "default_pay_cents": 2200,
        "tags": ["welcome-basket", "shop", "kcmo"],
    },
    "basket_assemble": {
        "title": "KC Welcome Basket — Assemble",
        "description": (
            "Assemble welcome basket per locked spec. Branded card + QR. "
            "Photo of finished basket required. "
            "PAY ON COMPLETION — assembly photo."
        ),
        "default_pay_cents": 2000,
        "tags": ["welcome-basket", "assemble", "kcmo"],
    },
    "basket_deliver": {
        "title": "KC Welcome Basket — Deliver to unit",
        "description": (
            "Place assembled basket inside STR unit at {address}. "
            "Photo proof inside unit. Text host done. "
            "PAY ON COMPLETION — placement photo."
        ),
        "default_pay_cents": 1800,
        "tags": ["welcome-basket", "deliver", "kcmo"],
    },
    "host_close_sale": {
        "title": "KC HOST CLOSE — {neighborhood} (World Cup blitz)",
        "description": (
            "CLOSE SALE AT DOOR. Visit STR host at {address}. "
            "Pitch welcome basket launch_5pack $249 (5 baskets) — ONLY {slots} slots left in KCMO. "
            "Host MUST pay on your phone (Stripe/GHL link) BEFORE you leave. "
            "Screenshot payment + photo with host. "
            "PAY ON COMPLETION — instant payout when host prepay confirmed. $45."
        ),
        "default_pay_cents": 4500,
        "tags": ["kc-blitz", "host-close", "sales", "kcmo"],
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
    slots_note = "30"
    if mission_type == "host_close_sale":
        from app.value_node.kc_blitz import blitz_status

        st = await blitz_status(db)
        slots_note = str(st["slots_remaining"])
    description = template["description"].format(
        neighborhood=neighborhood,
        address=target_address or "see briefing",
        slots=slots_note,
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


async def deploy_basket_crew(
    db: AsyncSession,
    *,
    host_id: int,
    neighborhood: str,
    target_address: str | None,
    basket_spec: str,
    dry_run: bool = True,
) -> list[dict]:
    """3-person crew: shop ($22) + assemble ($20) + deliver ($18). Commander can claim shopper gig."""
    spec_note = f"\n\nAGENT-LOCKED SPEC:\n{basket_spec[:2000]}"
    results = []
    for mission_type in ("basket_shop", "basket_assemble", "basket_deliver"):
        template = MISSION_TEMPLATES[mission_type]
        pay = template["default_pay_cents"]
        title = template["title"].format(neighborhood=neighborhood)
        description = template["description"].format(
            neighborhood=neighborhood,
            address=target_address or "host will confirm",
        ) + spec_note
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
            description=description + f"\nMission ID: {mission.id}. Pay on photo proof.",
            compensation=pay / 100,
            location=f"Kansas City, MO — {neighborhood}",
            tags=template["tags"],
            dry_run=dry_run,
        )
        if bounty.get("ok") and bounty.get("data"):
            mission.rentahuman_bounty_id = str(bounty["data"].get("id", ""))
            await db.commit()
        results.append(
            {
                "mission_type": mission_type,
                "mission_id": mission.id,
                "pay_cents": pay,
                "rentahuman": bounty,
            }
        )
    await trigger_n8n(
        "welcome-basket-crew",
        {"host_id": host_id, "missions": [r["mission_id"] for r in results]},
    )
    return results


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
