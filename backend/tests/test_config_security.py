import pytest
from pydantic import ValidationError
from app.core.config import Settings

def test_production_rejects_default_secrets():
    with pytest.raises(ValidationError):
        Settings(app_env="production", jwt_secret_key="change-me", webhook_hmac_secret="change-me")

def test_development_accepts_configured_secret():
    settings = Settings(app_env="development")
    assert settings.jwt_secret_key
