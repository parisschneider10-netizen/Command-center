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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
