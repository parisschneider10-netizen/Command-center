from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Command Center"
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite+aiosqlite:///./data/command_center.db"
    vapi_webhook_secret: str = ""
    portal_username: str = "commander"
    portal_password: str = "change-me"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    public_base_url: str = "http://localhost:8000"
    vault_path: str = "./vault"
    n8n_webhook_base_url: str = ""
    brave_search_api_key: str = ""
    rentahuman_api_key: str = ""
    commander_daily_budget_cap: float = 100.0
    guardian_per_task_cap: float = 25.0
    comms_imap_host: str = ""
    comms_imap_port: int = 993
    comms_imap_user: str = ""
    comms_imap_password: str = ""
    comms_smtp_host: str = ""
    comms_smtp_port: int = 587
    comms_smtp_user: str = ""
    comms_smtp_password: str = ""
    comms_from_name: str = "Commander"
    comms_auto_send_routine: bool = True
    servury_api_key: str = ""
    servury_api_url: str = "https://api.servury.com"
    ghl_api_key: str = ""
    ghl_api_url: str = "https://services.leadconnectorhq.com"
    ghl_company_id: str = ""
    ghl_mtr_recon_snapshot_id: str = ""
    openai_api_key: str = ""
    expansion_dry_run: bool = True
    expansion_max_cities: int = 40
    expansion_vps_cost_cents: int = 399
    expansion_live_batch_cap: int = 5
    treasury_hold_hours: int = 48
    treasury_ammo_percent: int = 70
    treasury_ops_reserve_percent: int = 30
    treasury_auto_fund_acquisitions: bool = True
    empire_tier_override: int = 0
    bridge_webhook_secret: str = ""
    bridge_allowed_senders: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
