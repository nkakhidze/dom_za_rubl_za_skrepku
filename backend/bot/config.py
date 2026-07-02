from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent


class BotSettings(BaseSettings):
    telegram_bot_token: str = "change_me"
    telegram_bot_username: str | None = None
    telegram_internal_api_token: str = "change_me"
    backend_base_url: str = "https://tomsk-dom-za-skrepku.space"
    backend_api_url: str | None = None
    public_site_url: str = "https://tomsk-dom-za-skrepku.space"

    model_config = SettingsConfigDict(
        env_file=(".env", BACKEND_ROOT / ".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def backend_url(self) -> str:
        return self.backend_api_url or self.backend_base_url


settings = BotSettings()
