"""Sovereign acquisition manifest — living list of empire capability targets."""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AmmoPool, SovereignAcquisition
from app.services import log_activity
from app.treasury.categories import (
    ACQUISITION_CATEGORIES,
    DEFAULT_ACQUISITIONS,
    DEFAULT_AMMO_WEIGHTS,
)


async def ensure_ammo_pools(db: AsyncSession) -> list[AmmoPool]:
    """Create ammo pool rows for each category if missing."""
    pools = []
    for category in ACQUISITION_CATEGORIES:
        result = await db.execute(select(AmmoPool).where(AmmoPool.category == category))
        pool = result.scalar_one_or_none()
        if not pool:
            pool = AmmoPool(category=category)
            db.add(pool)
        pools.append(pool)
    await db.commit()
    return pools


async def seed_default_acquisitions(db: AsyncSession) -> dict:
    """Seed sovereign acquisition manifest if empty."""
    count = await db.scalar(select(func.count()).select_from(SovereignAcquisition)) or 0
    if count > 0:
        return {"seeded": 0, "message": "Manifest already populated", "total": count}

    await ensure_ammo_pools(db)
    created = 0
    for item in DEFAULT_ACQUISITIONS:
        acq = SovereignAcquisition(
            category=item["category"],
            name=item["name"],
            description=item.get("description"),
            equipment_spec=item.get("equipment_spec"),
            target_cost_cents=item["target_cost_cents"],
            priority=item.get("priority", 5),
            empire_tier=item.get("empire_tier", 1),
            sovereign_required=True,
            vendor_candidates=item.get("vendor_candidates"),
            source_node="treasury",
            status="needed",
        )
        db.add(acq)
        created += 1
    await db.commit()
    await log_activity(db, "acquisitions_seeded", f"Seeded {created} sovereign acquisition targets")
    return {"seeded": created, "message": f"Seeded {created} acquisition targets"}


async def list_acquisitions(
    db: AsyncSession,
    *,
    category: str | None = None,
    status: str | None = None,
    empire_tier: int | None = None,
) -> list[SovereignAcquisition]:
    q = select(SovereignAcquisition).order_by(
        desc(SovereignAcquisition.priority),
        SovereignAcquisition.empire_tier,
    )
    if category:
        q = q.where(SovereignAcquisition.category == category)
    if status:
        q = q.where(SovereignAcquisition.status == status)
    if empire_tier is not None:
        q = q.where(SovereignAcquisition.empire_tier <= empire_tier)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_acquisition(db: AsyncSession, **fields) -> SovereignAcquisition:
    acq = SovereignAcquisition(**fields)
    db.add(acq)
    await db.commit()
    await db.refresh(acq)
    await log_activity(
        db,
        "acquisition_added",
        f"New target: {acq.name} ({acq.category})",
        {"id": acq.id, "target_cents": acq.target_cost_cents},
    )
    return acq


async def update_acquisition(
    db: AsyncSession, acq_id: int, **fields
) -> SovereignAcquisition | None:
    acq = await db.get(SovereignAcquisition, acq_id)
    if not acq:
        return None
    for key, value in fields.items():
        if value is not None and hasattr(acq, key):
            setattr(acq, key, value)
    acq.updated_at = datetime.now(timezone.utc)
    if fields.get("status") == "acquired":
        acq.acquired_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(acq)
    return acq


async def fund_acquisition_from_pool(
    db: AsyncSession,
    *,
    acquisition_id: int,
    amount_cents: int,
    category: str,
) -> SovereignAcquisition | None:
    """Move ammo from category pool into a specific acquisition target."""
    pool_result = await db.execute(select(AmmoPool).where(AmmoPool.category == category))
    pool = pool_result.scalar_one_or_none()
    if not pool or pool.balance_cents < amount_cents:
        raise ValueError(f"Insufficient ammo in {category} pool")

    acq = await db.get(SovereignAcquisition, acquisition_id)
    if not acq:
        return None

    pool.balance_cents -= amount_cents
    pool.updated_at = datetime.now(timezone.utc)
    acq.funded_cents += amount_cents
    acq.updated_at = datetime.now(timezone.utc)

    if acq.target_cost_cents > 0 and acq.funded_cents >= acq.target_cost_cents:
        acq.status = "funded"
    elif acq.funded_cents > 0:
        acq.status = "researching" if acq.status == "needed" else acq.status

    await db.commit()
    await db.refresh(acq)
    await log_activity(
        db,
        "acquisition_funded",
        f"${amount_cents / 100:.2f} ammo → {acq.name}",
        {"acquisition_id": acq.id, "funded_cents": acq.funded_cents},
    )
    return acq


async def auto_fund_top_priorities(db: AsyncSession) -> list[dict]:
    """Auto-allocate pool balances to highest-priority unfunded acquisitions per category."""
    if not settings.treasury_auto_fund_acquisitions:
        return []

    funded = []
    for category in ACQUISITION_CATEGORIES:
        pool_result = await db.execute(select(AmmoPool).where(AmmoPool.category == category))
        pool = pool_result.scalar_one_or_none()
        if not pool or pool.balance_cents <= 0:
            continue

        result = await db.execute(
            select(SovereignAcquisition)
            .where(
                SovereignAcquisition.category == category,
                SovereignAcquisition.status.in_(("needed", "researching")),
            )
            .order_by(desc(SovereignAcquisition.priority))
        )
        for acq in result.scalars().all():
            if pool.balance_cents <= 0:
                break
            remaining = max(0, acq.target_cost_cents - acq.funded_cents)
            if remaining <= 0:
                continue
            amount = min(pool.balance_cents, remaining)
            pool.balance_cents -= amount
            acq.funded_cents += amount
            if acq.funded_cents >= acq.target_cost_cents and acq.target_cost_cents > 0:
                acq.status = "funded"
            else:
                acq.status = "researching"
            funded.append({"id": acq.id, "name": acq.name, "amount_cents": amount})
        pool.updated_at = datetime.now(timezone.utc)

    if funded:
        await db.commit()
        await log_activity(
            db,
            "acquisitions_auto_funded",
            f"Auto-funded {len(funded)} acquisition target(s) from ammo pools",
        )
    return funded


def render_manifest_markdown(acquisitions: list[SovereignAcquisition], pools: list[AmmoPool]) -> str:
    """Render living manifest for vault sync."""
    now = datetime.now(timezone.utc).isoformat()
    pool_map = {p.category: p for p in pools}
    lines = [
        "# Sovereign Acquisition Manifest",
        "",
        "> Living document. Every revenue penny becomes ammo for empire capability.",
        f"> Last synced: {now}",
        "",
        "## Ammo pools (revenue → capability)",
        "",
        "| Category | Balance | Lifetime allocated | Purpose |",
        "|----------|---------|-------------------|---------|",
    ]
    for cat, purpose in ACQUISITION_CATEGORIES.items():
        pool = pool_map.get(cat)
        bal = f"${pool.balance_cents / 100:.2f}" if pool else "$0.00"
        total = f"${pool.allocated_total_cents / 100:.2f}" if pool else "$0.00"
        lines.append(f"| {cat} | {bal} | {total} | {purpose} |")

    lines.extend(
        [
            "",
            "## Acquisition queue",
            "",
            "| Priority | Tier | Category | Target | Funded | Status | Sovereign spec |",
            "|----------|------|----------|--------|--------|--------|----------------|",
        ]
    )
    for acq in acquisitions:
        target = f"${acq.target_cost_cents / 100:.2f}" if acq.target_cost_cents else "TBD"
        funded = f"${acq.funded_cents / 100:.2f}"
        spec = (acq.equipment_spec or "")[:80].replace("|", "/")
        lines.append(
            f"| {acq.priority} | T{acq.empire_tier} | {acq.category} | "
            f"{acq.name} | {target} / {funded} | {acq.status} | {spec} |"
        )

    lines.extend(
        [
            "",
            "## Agent instructions",
            "",
            "1. Research state-of-the-art **sovereign** options for each `needed` item.",
            "2. Prefer self-hosted, open-source, and vendor-independent paths.",
            "3. Update `vendor_candidates` via API when better options emerge.",
            "4. Network category: Starlink + Peplink = sovereign uplink independence.",
            "5. Commander approves `funded` → `ordered` → `acquired` (nuclear if over cap).",
            "",
            "## Revenue → ammo flow",
            "",
            f"- {settings.treasury_ammo_percent}% of cleared revenue → ammo pools (by category weight)",
            f"- {settings.treasury_ops_reserve_percent}% → ops reserve (worker payouts, immediate costs)",
            "- Sources: ground force host payments, laundry, expansion nodes, manual treasury inbound",
        ]
    )
    return "\n".join(lines) + "\n"


async def sync_manifest_to_vault(db: AsyncSession) -> Path:
    """Write manifest markdown to vault/commander/sovereign-acquisitions.md."""
    acquisitions = await list_acquisitions(db)
    pools = list(
        (await db.execute(select(AmmoPool).order_by(AmmoPool.category))).scalars().all()
    )
    content = render_manifest_markdown(acquisitions, pools)
    root = Path(settings.vault_path)
    commander_dir = root / "commander"
    commander_dir.mkdir(parents=True, exist_ok=True)
    path = commander_dir / "sovereign-acquisitions.md"
    path.write_text(content, encoding="utf-8")
    return path


async def acquisition_briefing(db: AsyncSession) -> dict:
    """Summary for portal and voice."""
    acquisitions = await list_acquisitions(db)
    pools = list(
        (await db.execute(select(AmmoPool).order_by(AmmoPool.category))).scalars().all()
    )
    needed = [a for a in acquisitions if a.status in ("needed", "researching")]
    funded = [a for a in acquisitions if a.status == "funded"]
    total_ammo = sum(p.balance_cents for p in pools)
    total_target = sum(a.target_cost_cents for a in acquisitions if a.target_cost_cents > 0)
    total_funded = sum(a.funded_cents for a in acquisitions)

    top_needs = sorted(needed, key=lambda a: (-a.priority, a.empire_tier))[:5]

    return {
        "ammo_balance_cents": total_ammo,
        "ammo_balance_usd": round(total_ammo / 100, 2),
        "acquisition_target_cents": total_target,
        "acquisition_funded_cents": total_funded,
        "needed_count": len(needed),
        "funded_ready_count": len(funded),
        "top_priorities": [
            {
                "id": a.id,
                "name": a.name,
                "category": a.category,
                "priority": a.priority,
                "empire_tier": a.empire_tier,
                "funded_cents": a.funded_cents,
                "target_cost_cents": a.target_cost_cents,
                "status": a.status,
                "equipment_spec": a.equipment_spec,
            }
            for a in top_needs
        ],
        "pools": [
            {
                "category": p.category,
                "balance_cents": p.balance_cents,
                "allocated_total_cents": p.allocated_total_cents,
            }
            for p in pools
        ],
        "allocation_rules": {
            "ammo_percent": settings.treasury_ammo_percent,
            "ops_reserve_percent": settings.treasury_ops_reserve_percent,
            "category_weights": DEFAULT_AMMO_WEIGHTS,
        },
    }
