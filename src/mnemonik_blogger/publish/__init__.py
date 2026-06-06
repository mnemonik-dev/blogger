"""Publisher registry: build the right Publisher for each platform from Settings."""

from __future__ import annotations

from ..config import Platform, Settings
from .base import Publisher
from .discord import DiscordPublisher
from .farcaster import FarcasterPublisher
from .telegram import TelegramPublisher
from .twitter import TwitterPublisher


def build_publisher(platform: Platform, settings: Settings) -> Publisher:
    dry = settings.dry_run
    if platform is Platform.TELEGRAM:
        return TelegramPublisher(settings.telegram, dry_run=dry)
    if platform is Platform.DISCORD:
        return DiscordPublisher(settings.discord, dry_run=dry)
    if platform is Platform.TWITTER:
        return TwitterPublisher(settings.twitter, dry_run=dry)
    if platform is Platform.FARCASTER:
        return FarcasterPublisher(settings.farcaster, dry_run=dry)
    raise ValueError(f"Unknown platform: {platform}")


__all__ = [
    "Publisher",
    "build_publisher",
    "TelegramPublisher",
    "DiscordPublisher",
    "TwitterPublisher",
    "FarcasterPublisher",
]
