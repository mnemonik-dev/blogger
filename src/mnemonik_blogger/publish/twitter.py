"""Publish a thread to X (Twitter) via API v2.

Uses tweepy (optional dependency, install with the ``twitter`` extra). Each
segment becomes a tweet; segments after the first reply to the previous one to
form a thread. X API write access requires a paid tier.
"""

from __future__ import annotations

from typing import Any

from ..config import Platform, TwitterConfig
from ..models import PublishResult, RenderedPost
from .base import dry_run_result


class TwitterPublisher:
    platform = Platform.TWITTER

    def __init__(self, config: TwitterConfig, *, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run

    def _client(self) -> Any:
        try:
            import tweepy
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "tweepy is required for X publishing: pip install 'mnemonik-blogger[twitter]'"
            ) from exc
        c = self.config
        return tweepy.Client(
            consumer_key=c.api_key.get_secret_value(),  # type: ignore[union-attr]
            consumer_secret=c.api_secret.get_secret_value(),  # type: ignore[union-attr]
            access_token=c.access_token.get_secret_value(),  # type: ignore[union-attr]
            access_token_secret=c.access_token_secret.get_secret_value(),  # type: ignore[union-attr]
        )

    def publish(self, post: RenderedPost) -> PublishResult:
        if self.dry_run:
            return dry_run_result(post)
        if not self.config.configured:
            return PublishResult(post.platform, ok=False, error="X (Twitter) not configured")

        try:
            client = self._client()
            ids: list[str] = []
            urls: list[str] = []
            reply_to: str | None = None
            for segment in post.segments:
                kwargs: dict[str, Any] = {"text": segment}
                if reply_to is not None:
                    kwargs["in_reply_to_tweet_id"] = reply_to
                resp = client.create_tweet(**kwargs)
                tweet_id = str(resp.data["id"])
                reply_to = tweet_id
                ids.append(tweet_id)
                urls.append(f"https://x.com/i/web/status/{tweet_id}")
        except Exception as exc:  # tweepy raises various error types
            return PublishResult(post.platform, ok=False, error=str(exc))

        return PublishResult(post.platform, ok=True, ids=ids, urls=urls)
