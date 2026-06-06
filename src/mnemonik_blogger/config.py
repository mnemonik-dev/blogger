"""Configuration and secret loading.

Enterprise-style secret handling: nothing is hardcoded. Every credential is read
from the environment (which a secret manager / fabric runner injects at deploy
time). Secrets are stored as ``pydantic.SecretStr`` so they never leak into logs,
reprs, or tracebacks. A ``.env`` file is supported for local development only and
is git-ignored.

Precedence (highest first):
    1. real process environment (what a secret manager injects)
    2. ``.env`` file in the working directory (local dev only)
    3. field defaults
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Platform(StrEnum):
    """Publishing targets supported in v1."""

    TELEGRAM = "telegram"
    DISCORD = "discord"
    TWITTER = "twitter"
    FARCASTER = "farcaster"


def _cfg(prefix: str | None = None) -> SettingsConfigDict:
    """Shared settings config; `prefix` namespaces a platform's env vars."""
    return SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_prefix=prefix or "",
    )


class _Base(BaseSettings):
    model_config = _cfg()


class TelegramConfig(_Base):
    model_config = _cfg("TELEGRAM_")

    bot_token: SecretStr | None = None
    # Channel to broadcast to, e.g. "@mnemonik" or a numeric -100... chat id.
    channel: str | None = None

    @property
    def configured(self) -> bool:
        return self.bot_token is not None and bool(self.channel)


class DiscordConfig(_Base):
    model_config = _cfg("DISCORD_")

    # Webhook is the simplest path; bot token + channel id is the alternative.
    webhook_url: SecretStr | None = None
    bot_token: SecretStr | None = None
    channel_id: str | None = None

    @property
    def configured(self) -> bool:
        return self.webhook_url is not None or (
            self.bot_token is not None and bool(self.channel_id)
        )


class TwitterConfig(_Base):
    model_config = _cfg("X_")

    api_key: SecretStr | None = None
    api_secret: SecretStr | None = None
    access_token: SecretStr | None = None
    access_token_secret: SecretStr | None = None

    @property
    def configured(self) -> bool:
        return all(
            v is not None
            for v in (self.api_key, self.api_secret, self.access_token, self.access_token_secret)
        )


class FarcasterConfig(_Base):
    model_config = _cfg("FARCASTER_")

    # Posting via Neynar managed signer (https://neynar.com).
    neynar_api_key: SecretStr | None = None
    signer_uuid: SecretStr | None = None

    @property
    def configured(self) -> bool:
        return self.neynar_api_key is not None and self.signer_uuid is not None


class Settings(_Base):
    """Top-level runtime configuration."""

    model_config = _cfg("MNEMONIK_")

    # Safety: default to dry-run so a misconfigured deploy never posts by accident.
    dry_run: bool = True
    # Path to a local protocol-facts file used when the Mnemonik MCP is unavailable.
    facts_path: str | None = None

    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    farcaster: FarcasterConfig = Field(default_factory=FarcasterConfig)

    def configured_platforms(self) -> list[Platform]:
        """Platforms that have complete credentials."""
        ready: list[Platform] = []
        if self.telegram.configured:
            ready.append(Platform.TELEGRAM)
        if self.discord.configured:
            ready.append(Platform.DISCORD)
        if self.twitter.configured:
            ready.append(Platform.TWITTER)
        if self.farcaster.configured:
            ready.append(Platform.FARCASTER)
        return ready


def load_settings() -> Settings:
    """Build settings from the environment / .env file."""
    return Settings()
