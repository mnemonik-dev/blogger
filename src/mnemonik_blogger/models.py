"""Core content data models.

The pipeline has one canonical unit (`SourcePost`) that the content layer renders
into one `RenderedPost` per platform. Publishers consume `RenderedPost` and return
a `PublishResult`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import Platform


@dataclass
class ProtocolFact:
    """A grounded, ideally attested, fact about the Mnemonik protocol."""

    text: str
    source: str = "manual"  # "mnemonik-mcp", "facts-file", or "manual"
    attestation_id: str | None = None
    verified: bool = False


@dataclass
class SourcePost:
    """The canonical content unit, platform-agnostic."""

    title: str
    body: str
    # Short hook / lead used by length-constrained platforms (X, Farcaster).
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    link: str | None = None
    facts: list[ProtocolFact] = field(default_factory=list)


@dataclass
class RenderedPost:
    """Platform-native rendering of a SourcePost.

    `segments` holds an ordered list of messages: a single element for one-shot
    platforms, multiple for threads (X / Farcaster / long Telegram).
    """

    platform: Platform
    segments: list[str]

    @property
    def is_thread(self) -> bool:
        return len(self.segments) > 1


@dataclass
class PublishResult:
    """Outcome of a publish attempt for one platform."""

    platform: Platform
    ok: bool
    dry_run: bool = False
    urls: list[str] = field(default_factory=list)
    ids: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def primary_url(self) -> str | None:
        return self.urls[0] if self.urls else None
