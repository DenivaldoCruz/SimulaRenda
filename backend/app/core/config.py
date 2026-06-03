from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str = Field(min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    CORS_ORIGINS: list[str] | str = Field(default_factory=list)
    nicegui_host: str = Field(default="0.0.0.0", validation_alias="NICEGUI_HOST")
    nicegui_port: int = Field(default=8000, validation_alias="NICEGUI_PORT")
    nicegui_storage_secret: str = Field(default="", validation_alias="NICEGUI_STORAGE_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def secret_key(self) -> str:
        """Return the application secret key using the lowercase settings convention."""
        return self.SECRET_KEY

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def set_storage_secret(self) -> "Settings":
        if not self.nicegui_storage_secret:
            self.nicegui_storage_secret = self.secret_key
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
