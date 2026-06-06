from __future__ import annotations

import pytest

from mnemonik_blogger.agent import run_campaign
from mnemonik_blogger.config import Platform, Settings
from mnemonik_blogger.content.generate import build_source_post
from mnemonik_blogger.grounding.mnemonik import StaticGrounding


def test_build_source_post_grounds_with_facts():
    post = build_source_post(
        title="Provable agent memory",
        brief="Agents forget. We fix that.",
        grounding=StaticGrounding(),
    )
    assert post.facts, "expected grounded facts"
    assert "Why it holds up" in post.body


def test_guardrail_blocks_banned_phrase():
    with pytest.raises(ValueError):
        build_source_post(title="100x guaranteed returns", brief="buy now")


def test_dry_run_campaign_does_not_publish():
    settings = Settings(dry_run=True)
    result = run_campaign(
        title="Hello Mnemonik",
        brief="A grounded update about verifiable memory.",
        platforms=list(Platform),
        settings=settings,
    )
    assert result.ok
    assert len(result.results) == len(list(Platform))
    assert all(r.dry_run for r in result.results)


def test_campaign_summary_lists_each_platform():
    settings = Settings(dry_run=True)
    result = run_campaign(
        title="Hello",
        brief="Body.",
        platforms=[Platform.TELEGRAM, Platform.TWITTER],
        settings=settings,
    )
    summary = result.summary()
    assert "telegram" in summary
    assert "twitter" in summary
