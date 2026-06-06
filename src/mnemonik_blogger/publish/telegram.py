"""Publish to a Telegram channel via the Bot API.

The bot must be an administrator of the target channel. Thread segments are sent
as sequential messages, each replying to the previous one.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..config import Platform, TelegramConfig
from ..models import PublishResult, RenderedPost
from .base import dry_run_result, with_retry

API = "https://api.telegram.org"


class TelegramPublisher:
    platform = Platform.TELEGRAM

    def __init__(self, config: TelegramConfig, *, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run

    def publish(self, post: RenderedPost) -> PublishResult:
        if self.dry_run:
            return dry_run_result(post)
        if not self.config.configured:
            return PublishResult(post.platform, ok=False, error="Telegram not configured")

        token = self.config.bot_token.get_secret_value()  # type: ignore[union-attr]
        url = f"{API}/bot{token}/sendMessage"
        ids: list[str] = []
        urls: list[str] = []
        reply_to: int | None = None
        try:
            with httpx.Client(timeout=30) as client:
                for segment in post.segments:
                    payload: dict[str, Any] = {
                        "chat_id": self.config.channel,
                        "text": segment,
                        "parse_mode": "MarkdownV2",
                        "disable_web_page_preview": False,
                    }
                    if reply_to is not None:
                        payload["reply_to_message_id"] = reply_to

                    def _send(payload: dict[str, Any] = payload) -> dict[str, Any]:
                        r = client.post(url, json=payload)
                        r.raise_for_status()
                        return r.json()  # type: ignore[no-any-return]

                    data = with_retry(_send)["result"]
                    msg_id = data["message_id"]
                    reply_to = msg_id
                    ids.append(str(msg_id))
                    chan = str(self.config.channel).lstrip("@")
                    urls.append(f"https://t.me/{chan}/{msg_id}")
        except httpx.HTTPError as exc:
            return PublishResult(post.platform, ok=False, error=str(exc), ids=ids, urls=urls)

        return PublishResult(post.platform, ok=True, ids=ids, urls=urls)
