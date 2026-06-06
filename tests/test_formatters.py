from __future__ import annotations

from mnemonik_blogger.config import Platform
from mnemonik_blogger.content import formatters
from mnemonik_blogger.content.formatters import (
    DISCORD_MAX,
    FARCASTER_MAX_BYTES,
    TELEGRAM_MAX,
    TWITTER_MAX,
)
from mnemonik_blogger.models import SourcePost


def _long_post() -> SourcePost:
    para = "Mnemonik gives agents memory they can prove. " * 20
    return SourcePost(
        title="Verifiable memory for AI agents",
        body="\n\n".join([para, para, para]),
        summary="Agents forget. Mnemonik makes memory provable.",
        tags=["#Mnemonik", "#AIagents"],
        link="https://mnemonik.xyz",
    )


def test_twitter_segments_within_limit():
    rendered = formatters.render(Platform.TWITTER, _long_post())
    assert rendered.is_thread
    for seg in rendered.segments:
        assert len(seg) <= TWITTER_MAX, seg


def test_twitter_thread_is_numbered():
    rendered = formatters.render(Platform.TWITTER, _long_post())
    assert rendered.segments[0].endswith(f"(1/{len(rendered.segments)})")


def test_telegram_within_limit_and_escaped():
    post = SourcePost(title="Hello. World!", body="a-b_c (test).", tags=["#x"])
    rendered = formatters.render(Platform.TELEGRAM, post)
    joined = "\n".join(rendered.segments)
    assert "\\." in joined  # MarkdownV2 escaping applied
    for seg in rendered.segments:
        assert len(seg) <= TELEGRAM_MAX


def test_discord_within_limit():
    rendered = formatters.render(Platform.DISCORD, _long_post())
    for seg in rendered.segments:
        assert len(seg) <= DISCORD_MAX


def test_farcaster_within_byte_limit():
    rendered = formatters.render(Platform.FARCASTER, _long_post())
    for seg in rendered.segments:
        assert len(seg.encode("utf-8")) <= FARCASTER_MAX_BYTES


def test_short_post_is_single_segment():
    post = SourcePost(title="Hi", body="Short body.", summary="Short.", tags=["#x"])
    rendered = formatters.render(Platform.TWITTER, post)
    assert len(rendered.segments) == 1
    assert "(1/" not in rendered.segments[0]
