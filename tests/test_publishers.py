from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from mnemonik_blogger.config import DiscordConfig, Platform, TelegramConfig
from mnemonik_blogger.models import RenderedPost
from mnemonik_blogger.publish import base
from mnemonik_blogger.publish.discord import DiscordPublisher
from mnemonik_blogger.publish.telegram import TelegramPublisher


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Make with_retry's backoff instant during tests.
    monkeypatch.setattr(base.time, "sleep", lambda *_: None)


def test_telegram_publish_sends_thread(monkeypatch):
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content)
        calls.append(payload)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": len(calls)}})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def fake_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", fake_client)

    cfg = TelegramConfig(bot_token=SecretStr("123:abc"), channel="@mnemonik")
    pub = TelegramPublisher(cfg, dry_run=False)
    post = RenderedPost(platform=Platform.TELEGRAM, segments=["one", "two", "three"])
    result = pub.publish(post)

    assert result.ok
    assert len(result.ids) == 3
    # Second and third messages thread under the previous one.
    assert calls[1]["reply_to_message_id"] == 1
    assert result.urls[0] == "https://t.me/mnemonik/1"


def test_discord_webhook_publish(monkeypatch):
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        seen.append(json.loads(request.content)["content"])
        return httpx.Response(200, json={"id": "999"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda *a, **k: real_client(*a, **{**k, "transport": transport}),
    )

    cfg = DiscordConfig(webhook_url=SecretStr("https://discord.com/api/webhooks/x/y"))
    pub = DiscordPublisher(cfg, dry_run=False)
    post = RenderedPost(platform=Platform.DISCORD, segments=["hello world"])
    result = pub.publish(post)

    assert result.ok
    assert seen == ["hello world"]


def test_unconfigured_publisher_fails_cleanly():
    pub = TelegramPublisher(TelegramConfig(), dry_run=False)
    result = pub.publish(RenderedPost(platform=Platform.TELEGRAM, segments=["x"]))
    assert not result.ok
    assert "not configured" in (result.error or "")
