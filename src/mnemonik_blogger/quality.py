"""Quality gate: score an article with claude-blog's analyzer before publishing.

The blogger does not write or score articles itself - that is claude-blog's job.
This module shells out to claude-blog's ``scripts/analyze_blog.py``, parses the
0-100 ``score.total``, and decides whether the article clears the configured
threshold.

It fails **closed**: any error (analyzer missing, non-zero exit, unparseable
output, missing/invalid score) yields a non-passing ``QualityReport`` so a broken
gate can never let unreviewed content through to a real publish.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Hard cap on the analyzer subprocess so a hung scorer can't wedge a publish.
_TIMEOUT_S = 120


@dataclass
class QualityReport:
    """Outcome of scoring one article against the quality threshold."""

    score: int
    threshold: int
    rating: str = ""
    issues: list[str] = field(default_factory=list)
    # Set when the gate could not be evaluated; ``passed`` is then always False.
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and self.score >= self.threshold

    def summary(self) -> str:
        if self.error:
            return f"quality gate ERROR (fail-closed): {self.error}"
        verdict = "PASS" if self.passed else "BLOCK"
        return (
            f"quality gate {verdict}: scored {self.score}/100 "
            f"(threshold {self.threshold}){f', rating {self.rating}' if self.rating else ''}"
        )


def _fail(threshold: int, error: str) -> QualityReport:
    return QualityReport(score=0, threshold=threshold, error=error)


def _format_issue(item: object) -> str:
    """Render an analyzer issue (a dict or a bare string) as one readable line."""
    if isinstance(item, dict):
        text = str(item.get("issue") or item.get("message") or "").strip()
        label = "/".join(str(item[k]) for k in ("severity", "category") if item.get(k))
        return f"[{label}] {text}" if label else text
    return str(item).strip()


def score_article(
    article: str | Path,
    *,
    claude_blog_path: str | Path | None,
    threshold: int,
) -> QualityReport:
    """Score ``article`` with claude-blog's analyzer; never raises (fail-closed)."""
    if not claude_blog_path:
        return _fail(threshold, "claude_blog_path is not configured")

    analyzer = Path(claude_blog_path) / "scripts" / "analyze_blog.py"
    if not analyzer.is_file():
        return _fail(threshold, f"analyzer not found at {analyzer}")

    article = Path(article)
    if not article.is_file():
        return _fail(threshold, f"article not found: {article}")

    try:
        proc = subprocess.run(
            [sys.executable, str(analyzer), str(article)],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return _fail(threshold, f"analyzer failed to run: {exc}")

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        tail = detail[-1] if detail else ""
        return _fail(threshold, f"analyzer exited {proc.returncode}: {tail[:200]}")

    try:
        block = json.loads(proc.stdout)["score"]
        total = int(block["total"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return _fail(threshold, f"could not parse analyzer output: {exc}")

    rating = str(block.get("rating", ""))
    issues = [s for s in (_format_issue(i) for i in block.get("issues", [])) if s][:10]
    return QualityReport(score=total, threshold=threshold, rating=rating, issues=issues)
