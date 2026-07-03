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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
