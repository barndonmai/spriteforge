from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SpriteForge"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(default="sqlite:///./spriteforge.db", validation_alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    storage_root: str = Field(default="storage", validation_alias="STORAGE_ROOT")
    provider: str = Field(default="mock", validation_alias="SPRITEFORGE_PROVIDER")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")
    gemini_image_model: str = Field(default="gemini-2.5-flash-image", validation_alias="GEMINI_IMAGE_MODEL")
    cors_origins: str = Field(default="http://localhost:3000", validation_alias="CORS_ORIGINS")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def storage_root_path(self) -> Path:
        configured_path = Path(self.storage_root)
        if configured_path.is_absolute():
            return configured_path
        return Path.cwd() / configured_path

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
