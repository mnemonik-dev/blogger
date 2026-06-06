from __future__ import annotations

import json
from pathlib import Path

from mnemonik_blogger.agent import run_campaign_from_article
from mnemonik_blogger.config import Platform, Settings
from mnemonik_blogger.quality import score_article

ARTICLE = """\
# Verifiable Memory for AI Agents

Agents forget, and you cannot prove what they recalled. Mnemonik makes every
memory a signed, verifiable attestation anchored on a public ledger.
"""


def _write_article(tmp_path: Path) -> Path:
    path = tmp_path / "article.md"
    path.write_text(ARTICLE, encoding="utf-8")
    return path


def _fake_claude_blog(tmp_path: Path, *, body: str) -> str:
    """Create a claude-blog checkout whose analyze_blog.py runs `body`."""
    root = tmp_path / "claude-blog"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "analyze_blog.py").write_text(body, encoding="utf-8")
    return str(root)


def _emit_score(score: int) -> str:
    payload = json.dumps({"score": {"total": score, "rating": "Publish", "issues": ["fix intro"]}})
    return f"print({payload!r})\n"


def test_score_passes_at_or_above_threshold(tmp_path: Path) -> None:
    cb = _fake_claude_blog(tmp_path, body=_emit_score(85))
    report = score_article(_write_article(tmp_path), claude_blog_path=cb, threshold=80)
    assert report.passed
    assert report.score == 85
    assert report.rating == "Publish"


def test_score_blocks_below_threshold(tmp_path: Path) -> None:
    cb = _fake_claude_blog(tmp_path, body=_emit_score(40))
    report = score_article(_write_article(tmp_path), claude_blog_path=cb, threshold=80)
    assert not report.passed
    assert report.error is None  # evaluated fine, just too low


def test_missing_claude_blog_path_fails_closed(tmp_path: Path) -> None:
    report = score_article(_write_article(tmp_path), claude_blog_path=None, threshold=80)
    assert not report.passed
    assert report.error is not None


def test_missing_analyzer_fails_closed(tmp_path: Path) -> None:
    empty = tmp_path / "empty-checkout"
    empty.mkdir()
    report = score_article(_write_article(tmp_path), claude_blog_path=str(empty), threshold=80)
    assert not report.passed
    assert "analyzer not found" in (report.error or "")


def test_bad_json_fails_closed(tmp_path: Path) -> None:
    cb = _fake_claude_blog(tmp_path, body="print('not json')\n")
    report = score_article(_write_article(tmp_path), claude_blog_path=cb, threshold=80)
    assert not report.passed
    assert "parse" in (report.error or "")


def test_analyzer_nonzero_exit_fails_closed(tmp_path: Path) -> None:
    cb = _fake_claude_blog(tmp_path, body="import sys\nsys.exit(2)\n")
    report = score_article(_write_article(tmp_path), claude_blog_path=cb, threshold=80)
    assert not report.passed
    assert "exited 2" in (report.error or "")


def test_campaign_publishes_when_gate_passes(tmp_path: Path) -> None:
    cb = _fake_claude_blog(tmp_path, body=_emit_score(90))
    settings = Settings(dry_run=True, claude_blog_path=cb, min_score=80)
    result = run_campaign_from_article(
        article=_write_article(tmp_path),
        platforms=[Platform.TELEGRAM, Platform.TWITTER],
        settings=settings,
    )
    assert result.ok
    assert not result.blocked
    assert len(result.results) == 2
    assert all(r.dry_run for r in result.results)


def test_campaign_blocks_and_publishes_nothing_when_gate_fails(tmp_path: Path) -> None:
    cb = _fake_claude_blog(tmp_path, body=_emit_score(10))
    settings = Settings(dry_run=True, claude_blog_path=cb, min_score=80)
    result = run_campaign_from_article(
        article=_write_article(tmp_path),
        platforms=list(Platform),
        settings=settings,
    )
    assert result.blocked
    assert not result.ok
    assert result.results == []
    assert "BLOCKED" in result.summary()
