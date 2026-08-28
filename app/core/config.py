from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_test_db: str
    postgres_host: str
    postgres_port: int
    secret_key: str
    cors_origins: str
    frontend_url: str = "http://localhost:5173"
    password_reset_token_ttl_minutes: int = 30
    email_verify_token_ttl_minutes: int = 1440

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def test_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_test_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
