import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    blocked = "blocked"
    cancelled = "cancelled"


class TaskPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.pending
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.normal
    )
    source: Mapped[str] = mapped_column(String(64), default="voice")
    open_for_agents: Mapped[bool] = mapped_column(default=True)
    claimed_by_agent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    will_priority: Mapped[int] = mapped_column(Integer, default=5)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vapi_call_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    context: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentWorker(Base):
    __tablename__ = "agent_workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    agent_type: Mapped[str] = mapped_column(String(64), default="custom")
    capabilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(16), default="inbound")
    from_addr: Mapped[str] = mapped_column(String(255))
    to_addr: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(512))
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="received")
    agent_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    nuclear_flag: Mapped[bool] = mapped_column(default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AgentWallet(Base):
    __tablename__ = "agent_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    daily_limit_cents: Mapped[int] = mapped_column(Integer, default=5000)
    daily_spent_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TreasuryLedger(Base):
    __tablename__ = "treasury_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    direction: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    a2a_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    nuclear_required: Mapped[bool] = mapped_column(default=False)
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linked_mission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ScrapedLead(Base):
    """Property manager lead — STR recon / GHL SaaS expansion pipeline."""

    __tablename__ = "scraped_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    city: Mapped[str] = mapped_column(String(128), index=True)
    crisis_type: Mapped[str] = mapped_column(String(64), default="Unautomated-STR-Leak")
    status: Mapped[str] = mapped_column(String(64), default="scraped")
    servury_server_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    servury_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ghl_account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class LaundryHost(Base):
    __tablename__ = "laundry_hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    unit_count: Mapped[int] = mapped_column(Integer, default=1)
    offers_luggage_valet: Mapped[bool] = mapped_column(default=False)
    storage_units_available: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(64), default="lead")
    ghl_contact_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    welcome_basket_credits: Mapped[int] = mapped_column(Integer, default=0)
    prepaid_balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    locked_basket_spec: Mapped[str | None] = mapped_column(Text, nullable=True)
    program: Mapped[str] = mapped_column(String(64), default="laundry")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WelcomeBasketFulfillment(Base):
    """One welcome basket cycle — host prepaid, agents lock spec, humans fulfill."""

    __tablename__ = "welcome_basket_fulfillments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_id: Mapped[int] = mapped_column(Integer, index=True)
    basket_spec: Mapped[str] = mapped_column(Text)
    revenue_cents: Mapped[int] = mapped_column(Integer, default=0)
    labor_budget_cents: Mapped[int] = mapped_column(Integer, default=6000)
    status: Mapped[str] = mapped_column(String(32), default="planned")
    shop_mission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deliver_mission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LaundryGuestRequest(Base):
    __tablename__ = "laundry_guest_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pickup_address: Mapped[str] = mapped_column(Text)
    service_type: Mapped[str] = mapped_column(String(64), default="laundry_turn")
    status: Mapped[str] = mapped_column(String(64), default="requested")
    rentahuman_bounty_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    revenue_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GroundForceMission(Base):
    __tablename__ = "ground_force_missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mission_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    neighborhood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    pay_on_completion_cents: Mapped[int] = mapped_column(Integer, default=2500)
    status: Mapped[str] = mapped_column(String(64), default="open")
    rentahuman_bounty_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    host_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proof_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    host_payment_ledger_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EscalationLevel(str, enum.Enum):
    agent = "agent"
    human = "human"
    commander = "commander"


class EscalationStatus(str, enum.Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    needs_commander = "needs_commander"


class Guardian(Base):
    __tablename__ = "guardians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(64), default="guardian")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rentahuman_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    max_per_task: Mapped[float] = mapped_column(Float, default=25.0)
    is_active: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SovereignAcquisition(Base):
    """Equipment and infrastructure the empire must acquire — funded by revenue ammo."""

    __tablename__ = "sovereign_acquisitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_spec: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    funded_cents: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="needed")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    empire_tier: Mapped[int] = mapped_column(Integer, default=1)
    sovereign_required: Mapped[bool] = mapped_column(default=True)
    vendor_candidates: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_node: Mapped[str] = mapped_column(String(64), default="treasury")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AmmoPool(Base):
    """Per-category ammo balance — revenue transformed into empire capability."""

    __tablename__ = "ammo_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    allocated_total_cents: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AmmoAllocation(Base):
    """Ledger of revenue → ammo transformations."""

    __tablename__ = "ammo_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_ledger_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    acquisition_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CommanderIntent(Base):
    """Commander stated goal — system returns plan, hive + firewall execute."""

    __tablename__ = "commander_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intent_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="commander")
    status: Mapped[str] = mapped_column(String(32), default="planned")
    template_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntentMicroTask(Base):
    """Decomposed micro-task from intent — agent, guardian, or RentAHuman."""

    __tablename__ = "intent_micro_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intent_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    executor: Mapped[str] = mapped_column(String(32), default="agent")
    budget_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    will_priority: Mapped[int] = mapped_column(Integer, default=6)
    status: Mapped[str] = mapped_column(String(32), default="planned")
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linked_escalation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rentahuman_bounty_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class JudgmentRule(Base):
    """What requires human judgment vs agent-only — Commander configures."""

    __tablename__ = "judgment_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_key: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str] = mapped_column(String(255))
    handler: Mapped[str] = mapped_column(String(32))
    auto_post_rah: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CityCap(Base):
    """Per-city unit cap — KCMO World Cup blitz: 30 units max."""

    __tablename__ = "city_caps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    city_name: Mapped[str] = mapped_column(String(128))
    max_units: Mapped[int] = mapped_column(Integer, default=30)
    program: Mapped[str] = mapped_column(String(64), default="welcome_basket")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KcHostLead(Base):
    """AI-scraped KC STR host lead — ground force closes sale on-site."""

    __tablename__ = "kc_host_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    listing_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    unit_count: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(64), default="ai_scrape")
    status: Mapped[str] = mapped_column(String(32), default="new")
    mission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    host_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    package_sku: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SovereignHost(Base):
    """Sovereign Stay host — Layer 1 lock-in, badges, buyback target."""

    __tablename__ = "sovereign_hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    host_name: Mapped[str] = mapped_column(String(255))
    property_address: Mapped[str] = mapped_column(Text)
    city_grid: Mapped[str] = mapped_column(String(128), index=True)
    city_code: Mapped[str] = mapped_column(String(32), index=True)
    badges_json: Mapped[str] = mapped_column(Text, default='["FREE_CHECKOUT_RIDE","VERIFIED_MATCHDAY_WASH"]')
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE_LOCK_IN")
    gross_collected_cents: Mapped[int] = mapped_column(Integer, default=0)
    closer_cut_cents: Mapped[int] = mapped_column(Integer, default=0)
    net_float_cents: Mapped[int] = mapped_column(Integer, default=0)
    cursor_earmark_cents: Mapped[int] = mapped_column(Integer, default=0)
    vault_reserve_cents: Mapped[int] = mapped_column(Integer, default=0)
    vacancy_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    inbound_ledger_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closer_mission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SovereignLedgerEvent(Base):
    """Append-only DeFi-style audit trail — immutable VPS ledger."""

    __tablename__ = "sovereign_ledger_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    host_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SovereignCloserPayout(Base):
    """Closer pay queue — bootstrap defers; paid from host-funded treasury or host direct."""

    __tablename__ = "sovereign_closer_payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    host_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closer_wallet: Mapped[str] = mapped_column(String(128))
    amount_cents: Mapped[int] = mapped_column(Integer, default=3000)
    status: Mapped[str] = mapped_column(String(32), default="deferred")
    payment_mode: Mapped[str] = mapped_column(String(32), default="bootstrap")
    payout_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HumanEscalation(Base):
    __tablename__ = "human_escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    level: Mapped[EscalationLevel] = mapped_column(
        Enum(EscalationLevel), default=EscalationLevel.human
    )
    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus), default=EscalationStatus.open
    )
    task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    guardian_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rentahuman_bounty_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    nuclear_flag: Mapped[bool] = mapped_column(default=False)
    source: Mapped[str] = mapped_column(String(64), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
