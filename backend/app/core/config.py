from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str

    db_echo: bool = False

    upload_dir: str = "uploads"
    public_base_url: str = "http://127.0.0.1:8000"
    max_upload_size_mb: int = 5
    admin_api_token: str = "change_me"
    allow_admin_token_auth: bool = True
    allow_admin_token_fallback: bool | None = None
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    dev_mode: bool = False
    telegram_bot_token: str = "change_me"
    backend_api_url: str = "http://127.0.0.1:8000"
    cors_origins: list[str] = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def model_post_init(self, __context: object) -> None:
        if self.allow_admin_token_fallback is not None:
            self.allow_admin_token_auth = self.allow_admin_token_fallback

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
