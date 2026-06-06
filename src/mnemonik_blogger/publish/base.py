"""Publisher protocol, retry helper, and dry-run support."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol, TypeVar

import httpx

from ..config import Platform
from ..models import PublishResult, RenderedPost

T = TypeVar("T")


class Publisher(Protocol):
    platform: Platform

    def publish(self, post: RenderedPost) -> PublishResult: ...


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call `fn`, retrying transient HTTP/network errors with exponential backoff."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            last = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            # Don't retry client errors except rate-limiting.
            if status is not None and 400 <= status < 500 and status != 429:
                raise
            if attempt < attempts - 1:
                sleep(base_delay * (2**attempt))
    assert last is not None
    raise last


def dry_run_result(post: RenderedPost) -> PublishResult:
    return PublishResult(platform=post.platform, ok=True, dry_run=True)
