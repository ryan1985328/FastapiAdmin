"""Focused tests for the production fail-closed configuration boundary."""

import pytest
from pydantic import ValidationError

from app.common.enums import EnvironmentEnum
from app.config.setting import Settings
from app.scripts.initialize import InitializeData


def valid_production_settings(**overrides) -> Settings:
    values = {
        "ENVIRONMENT": EnvironmentEnum.PROD,
        "DEBUG": False,
        "SECRET_KEY": "gate3-production-secret-key-with-at-least-32-bytes",
        "PROD_CORS_ORIGINS": "https://admin.example.com",
        "ALLOW_METHODS": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "ALLOW_HEADERS": ["Authorization", "Content-Type", "X-Request-ID"],
        "ALLOW_CREDENTIALS": True,
        "ALLOWED_HOSTS": ["admin.example.com", "api.example.com"],
        "OAUTH_ALLOWED_HOSTS": ["admin.example.com"],
        "APP_SMS_FIXED_CODE_ENABLED": False,
    }
    values.update(overrides)
    return Settings(**values)


def test_development_defaults_remain_convenient():
    settings = Settings(ENVIRONMENT=EnvironmentEnum.DEV)

    assert settings.DEBUG is True
    assert settings.SECRET_KEY
    assert settings.ALLOW_ORIGINS == ["*"]


def test_valid_production_settings_are_accepted():
    assert valid_production_settings().ENVIRONMENT == EnvironmentEnum.PROD


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("DEBUG", True, "DEBUG"),
        ("SECRET_KEY", "fastapi-admin-starter-dev-secret-key-do-not-use-in-production", "SECRET_KEY"),
        ("PROD_CORS_ORIGINS", "", "PROD_CORS_ORIGINS"),
        ("PROD_CORS_ORIGINS", "*", "PROD_CORS_ORIGINS"),
        ("ALLOW_METHODS", ["*"], "ALLOW_METHODS"),
        ("ALLOW_HEADERS", ["*"], "ALLOW_HEADERS"),
        ("OAUTH_ALLOWED_HOSTS", ["*"], "OAUTH_ALLOWED_HOSTS"),
        ("ALLOWED_HOSTS", ["*"], "ALLOWED_HOSTS"),
        ("APP_SMS_FIXED_CODE_ENABLED", True, "APP_SMS_FIXED_CODE_ENABLED"),
    ],
)
def test_known_unsafe_production_defaults_are_rejected(field, value, message):
    with pytest.raises(ValidationError, match=message):
        valid_production_settings(**{field: value})


def test_oauth_local_fallback_is_rejected_when_oauth_is_configured():
    with pytest.raises(ValidationError, match="OAUTH_FRONTEND_FALLBACK"):
        valid_production_settings(OAUTH_GITHUB_CLIENT_ID="configured-client")


def test_production_initialization_rejects_empty_user_table(monkeypatch):
    from app.config.setting import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentEnum.PROD)

    with pytest.raises(RuntimeError, match="默认 seed 创建管理员"):
        InitializeData._ensure_production_admin_seed_safe(0)


def test_production_initialization_allows_preprovisioned_user(monkeypatch):
    from app.config.setting import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentEnum.PROD)
    InitializeData._ensure_production_admin_seed_safe(1)


def test_development_initialization_keeps_seed_behavior(monkeypatch):
    from app.config.setting import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentEnum.DEV)
    InitializeData._ensure_production_admin_seed_safe(0)
