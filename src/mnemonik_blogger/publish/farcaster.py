"""Publish a cast (thread) to Farcaster via the Neynar API.

Requires a Neynar API key and a managed signer UUID. Segments after the first
are posted as replies to the previous cast to form a thread.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..config import FarcasterConfig, Platform
from ..models import PublishResult, RenderedPost
from .base import dry_run_result, with_retry

API = "https://api.neynar.com/v2/farcaster/cast"


class FarcasterPublisher:
    platform = Platform.FARCASTER

    def __init__(self, config: FarcasterConfig, *, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run

    def publish(self, post: RenderedPost) -> PublishResult:
        if self.dry_run:
            return dry_run_result(post)
        if not self.config.configured:
            return PublishResult(post.platform, ok=False, error="Farcaster not configured")

        headers = {
            "api_key": self.config.neynar_api_key.get_secret_value(),  # type: ignore[union-attr]
            "content-type": "application/json",
        }
        signer = self.config.signer_uuid.get_secret_value()  # type: ignore[union-attr]
        ids: list[str] = []
        urls: list[str] = []
        parent: str | None = None
        try:
            with httpx.Client(timeout=30, headers=headers) as client:
                for segment in post.segments:
                    payload: dict[str, Any] = {"signer_uuid": signer, "text": segment}
                    if parent is not None:
                        payload["parent"] = parent

                    def _send(payload: dict[str, Any] = payload) -> dict[str, Any]:
                        r = client.post(API, json=payload)
                        r.raise_for_status()
                        return r.json()  # type: ignore[no-any-return]

                    cast = with_retry(_send)["cast"]
                    cast_hash = cast["hash"]
                    parent = cast_hash
                    ids.append(cast_hash)
                    urls.append(f"https://warpcast.com/~/conversations/{cast_hash}")
        except httpx.HTTPError as exc:
            return PublishResult(post.platform, ok=False, error=str(exc), ids=ids, urls=urls)

        return PublishResult(post.platform, ok=True, ids=ids, urls=urls)
