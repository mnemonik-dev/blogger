"""Publish to a Discord channel.

Prefers a channel webhook (no bot, simplest). Falls back to the Bot API
(create-message) when a bot token + channel id are configured.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..config import DiscordConfig, Platform
from ..models import PublishResult, RenderedPost
from .base import dry_run_result, with_retry

API = "https://discord.com/api/v10"


class DiscordPublisher:
    platform = Platform.DISCORD

    def __init__(self, config: DiscordConfig, *, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run

    def publish(self, post: RenderedPost) -> PublishResult:
        if self.dry_run:
            return dry_run_result(post)
        if not self.config.configured:
            return PublishResult(post.platform, ok=False, error="Discord not configured")

        try:
            if self.config.webhook_url is not None:
                return self._via_webhook(post)
            return self._via_bot(post)
        except httpx.HTTPError as exc:
            return PublishResult(post.platform, ok=False, error=str(exc))

    def _via_webhook(self, post: RenderedPost) -> PublishResult:
        url = self.config.webhook_url.get_secret_value()  # type: ignore[union-attr]
        ids: list[str] = []
        with httpx.Client(timeout=30) as client:
            for segment in post.segments:

                def _send(segment: str = segment) -> dict[str, Any]:
                    # wait=true makes Discord return the created message object.
                    r = client.post(url, params={"wait": "true"}, json={"content": segment})
                    r.raise_for_status()
                    return r.json()  # type: ignore[no-any-return]

                ids.append(str(with_retry(_send).get("id", "")))
        return PublishResult(post.platform, ok=True, ids=ids)

    def _via_bot(self, post: RenderedPost) -> PublishResult:
        token = self.config.bot_token.get_secret_value()  # type: ignore[union-attr]
        headers = {"Authorization": f"Bot {token}"}
        endpoint = f"{API}/channels/{self.config.channel_id}/messages"
        ids: list[str] = []
        with httpx.Client(timeout=30, headers=headers) as client:
            for segment in post.segments:

                def _send(segment: str = segment) -> dict[str, Any]:
                    r = client.post(endpoint, json={"content": segment})
                    r.raise_for_status()
                    return r.json()  # type: ignore[no-any-return]

                ids.append(str(with_retry(_send)["id"]))
        return PublishResult(post.platform, ok=True, ids=ids)
