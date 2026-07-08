from app.core.config import Settings, get_settings


def test_default_settings() -> None:
    settings = Settings(_env_file=None)

    assert settings.APP_NAME == "Insight Forge"
    assert settings.APP_VERSION == "2.0.0"
    assert settings.APP_ENV == "development"
    assert settings.DATABASE_URL == ""
    assert settings.JWT_ALGORITHM == "RS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15


def test_get_settings_is_cached() -> None:
    first = get_settings()
    second = get_settings()

    assert first is second