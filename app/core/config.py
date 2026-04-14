from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Logistics Driver Tracking"
    debug: bool = False

    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/logistic")
    redis_url: str = Field(default="redis://redis:6379/0")

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:19006"]


settings = Settings()
