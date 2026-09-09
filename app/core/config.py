from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "production"] = "development"
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    secret_key: str
    cors_origins: str
    resend_api_key: str
    resend_from_email: str = "onboarding@resend.dev"
    frontend_url: str = "http://localhost:5173"
    password_reset_code_ttl_minutes: int = 15
    email_verify_code_ttl_minutes: int = 30
    resend_cooldown_seconds: int = 60
    verification_code_max_attempts: int = 5
    password_reset_confirmation_ttl_minutes: int = 10

    model_config = SettingsConfigDict(env_file=".env.test")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
