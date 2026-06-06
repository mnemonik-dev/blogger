from __future__ import annotations

from mnemonik_blogger.config import Platform, Settings


def test_no_credentials_means_no_configured_platforms(monkeypatch):
    # Ensure a clean environment with no platform credentials.
    for var in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHANNEL",
        "DISCORD_WEBHOOK_URL",
        "DISCORD_BOT_TOKEN",
        "X_API_KEY",
        "FARCASTER_NEYNAR_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)
    settings = Settings(_env_file=None)
    assert settings.configured_platforms() == []


def test_telegram_detected_when_credentials_present(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHANNEL", "@mnemonik")
    settings = Settings(_env_file=None)
    assert Platform.TELEGRAM in settings.configured_platforms()


def test_secret_not_in_repr(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "supersecret")
    monkeypatch.setenv("TELEGRAM_CHANNEL", "@mnemonik")
    settings = Settings(_env_file=None)
    assert "supersecret" not in repr(settings.telegram)


def test_default_is_dry_run():
    assert Settings(_env_file=None).dry_run is True
