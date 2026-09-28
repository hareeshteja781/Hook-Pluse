from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "hook-pluse"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres:change-me@localhost:5433/hook_pluse"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    webhook_hmac_secret: str = "change-me"
    max_delivery_attempts: int = 5
    retry_base_seconds: int = 2

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.app_env.lower() == "production" and (self.jwt_secret_key == "change-me" or self.webhook_hmac_secret == "change-me"):
            raise ValueError("Production requires non-default JWT and webhook secrets")
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
