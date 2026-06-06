"""Render a SourcePost into platform-native RenderedPosts.

Each platform has its own length budget, markup rules, and thread conventions.
The splitter prefers paragraph then sentence boundaries so segments read cleanly.
"""

from __future__ import annotations

import re

from ..config import Platform
from ..models import RenderedPost, SourcePost
from . import voice

# Platform limits (characters unless noted).
TELEGRAM_MAX = 4096
DISCORD_MAX = 2000
TWITTER_MAX = 280
FARCASTER_MAX_BYTES = 1024

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
# Telegram MarkdownV2 reserved characters that must be backslash-escaped.
_TG_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def _pack(units: list[str], max_len: int, joiner: str = "\n\n") -> list[str]:
    """Greedily pack units into segments no longer than max_len."""
    segments: list[str] = []
    current = ""
    for unit in units:
        candidate = unit if not current else current + joiner + unit
        if len(candidate) <= max_len:
            current = candidate
            continue
        if current:
            segments.append(current)
        # Unit alone is too big: fall back to sentence, then hard splitting.
        if len(unit) <= max_len:
            current = unit
        else:
            for piece in _hard_split(unit, max_len):
                segments.append(piece)
            current = ""
    if current:
        segments.append(current)
    return segments or [""]


def _hard_split(text: str, max_len: int) -> list[str]:
    """Split overlong text on sentence boundaries, then on width as a last resort."""
    out: list[str] = []
    buf = ""
    for sentence in _SENTENCE_RE.split(text):
        candidate = sentence if not buf else buf + " " + sentence
        if len(candidate) <= max_len:
            buf = candidate
        else:
            if buf:
                out.append(buf)
            while len(sentence) > max_len:
                out.append(sentence[:max_len])
                sentence = sentence[max_len:]
            buf = sentence
    if buf:
        out.append(buf)
    return out


def _escape_telegram(text: str) -> str:
    return "".join("\\" + ch if ch in _TG_SPECIAL else ch for ch in text)


def _tagline(tags: list[str]) -> str:
    chosen = tags or voice.HASHTAGS[:3]
    return " ".join(t if t.startswith("#") else f"#{t}" for t in chosen)


def render_telegram(post: SourcePost) -> RenderedPost:
    head = f"*{_escape_telegram(post.title)}*"
    units = [head] + [_escape_telegram(p) for p in _paragraphs(post.body)]
    if post.link:
        units.append(_escape_telegram(post.link))
    units.append(_escape_telegram(_tagline(post.tags)))
    segments = _pack(units, TELEGRAM_MAX)
    return RenderedPost(platform=Platform.TELEGRAM, segments=segments)


def render_discord(post: SourcePost) -> RenderedPost:
    head = f"**{post.title}**"
    units = [head] + _paragraphs(post.body)
    if post.link:
        units.append(post.link)
    units.append(_tagline(post.tags))
    segments = _pack(units, DISCORD_MAX)
    return RenderedPost(platform=Platform.DISCORD, segments=segments)


def _lead_units(lead: str, body: str) -> list[str]:
    """Lead followed by body paragraphs, without repeating the lead."""
    paras = _paragraphs(body)
    if paras and paras[0].strip() == lead.strip():
        return paras
    return [lead, *paras]


def render_twitter(post: SourcePost) -> RenderedPost:
    lead = post.summary or post.title
    # Reserve room for a trailing " (n/N)" counter.
    body_budget = TWITTER_MAX - 8
    units = _lead_units(lead, post.body)
    if post.link:
        units.append(post.link)
    units.append(_tagline(post.tags))
    raw = _pack(units, body_budget, joiner="\n\n")
    total = len(raw)
    segments = [f"{seg} ({i}/{total})" if total > 1 else seg for i, seg in enumerate(raw, 1)]
    return RenderedPost(platform=Platform.TWITTER, segments=segments)


def _byte_pack(units: list[str], max_bytes: int) -> list[str]:
    segments: list[str] = []
    current = ""
    for unit in units:
        candidate = unit if not current else current + "\n\n" + unit
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
        else:
            if current:
                segments.append(current)
            current = unit
    if current:
        segments.append(current)
    return segments or [""]


def render_farcaster(post: SourcePost) -> RenderedPost:
    lead = post.summary or post.title
    units = _lead_units(lead, post.body)
    if post.link:
        units.append(post.link)
    units.append(_tagline(post.tags))
    segments = _byte_pack(units, FARCASTER_MAX_BYTES)
    return RenderedPost(platform=Platform.FARCASTER, segments=segments)


_RENDERERS = {
    Platform.TELEGRAM: render_telegram,
    Platform.DISCORD: render_discord,
    Platform.TWITTER: render_twitter,
    Platform.FARCASTER: render_farcaster,
}


def render(platform: Platform, post: SourcePost) -> RenderedPost:
    return _RENDERERS[platform](post)
