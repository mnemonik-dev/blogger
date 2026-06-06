"""The blogger agent: ground -> generate -> render -> publish -> attest.

This is the orchestration entry point used by both the CLI and a fabric runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import Platform, Settings
from .content.generate import build_source_post, render_all
from .content.ingest import ingest_article
from .grounding.mnemonik import Grounding, default_grounding
from .models import PublishResult, SourcePost
from .publish import build_publisher
from .quality import QualityReport, score_article


@dataclass
class CampaignResult:
    post: SourcePost
    results: list[PublishResult] = field(default_factory=list)
    # Set for article-based campaigns; None for direct brief-based campaigns.
    quality: QualityReport | None = None
    # True when the quality gate blocked publishing (results is then empty).
    blocked: bool = False

    @property
    def ok(self) -> bool:
        return not self.blocked and all(r.ok for r in self.results)

    def summary(self) -> str:
        lines = [f"# {self.post.title}"]
        if self.quality is not None:
            lines.append(self.quality.summary())
        if self.blocked:
            lines.append("BLOCKED: quality gate not met - nothing was published.")
            for issue in self.quality.issues if self.quality else []:
                lines.append(f"  - {issue}")
        for r in self.results:
            status = "DRY-RUN" if r.dry_run else ("OK" if r.ok else "FAIL")
            extra = r.primary_url or r.error or ""
            lines.append(f"- {r.platform.value:9} {status:8} {extra}")
        return "\n".join(lines)


def run_campaign(
    *,
    title: str,
    brief: str,
    platforms: list[Platform],
    settings: Settings,
    link: str | None = None,
    tags: list[str] | None = None,
    grounding: Grounding | None = None,
    attest: bool = True,
) -> CampaignResult:
    """Generate one grounded post and publish it to each platform."""
    grounding = grounding or default_grounding(settings.facts_path)

    post = build_source_post(title=title, brief=brief, link=link, tags=tags, grounding=grounding)
    results = _publish_post(post, platforms, settings, grounding, attest=attest)
    return CampaignResult(post=post, results=results)


def run_campaign_from_article(
    *,
    article: str | Path,
    platforms: list[Platform],
    settings: Settings,
    grounding: Grounding | None = None,
    attest: bool = True,
    min_score: int | None = None,
) -> CampaignResult:
    """Publish a finished Markdown article, but only if it clears the quality gate.

    The article is scored by claude-blog's analyzer. If ``score.total`` is below
    the threshold (or the gate cannot be evaluated), nothing is published and the
    result is marked ``blocked``. The gate fails closed.
    """
    threshold = settings.min_score if min_score is None else min_score
    report = score_article(article, claude_blog_path=settings.claude_blog_path, threshold=threshold)

    # ingest_article enforces guardrails; do it before any publish.
    post = ingest_article(article)

    if not report.passed:
        return CampaignResult(post=post, results=[], quality=report, blocked=True)

    grounding = grounding or default_grounding(settings.facts_path)
    results = _publish_post(post, platforms, settings, grounding, attest=attest)
    return CampaignResult(post=post, results=results, quality=report)


def _publish_post(
    post: SourcePost,
    platforms: list[Platform],
    settings: Settings,
    grounding: Grounding,
    *,
    attest: bool,
) -> list[PublishResult]:
    """Render and publish a post to each platform, then optionally attest."""
    rendered = render_all(post, platforms)
    results: list[PublishResult] = []
    for platform in platforms:
        publisher = build_publisher(platform, settings)
        results.append(publisher.publish(rendered[platform]))

    if attest and not settings.dry_run:
        published = [r for r in results if r.ok and not r.dry_run]
        if published:
            record = f"Published '{post.title}' to: " + ", ".join(
                f"{r.platform.value} ({r.primary_url or ', '.join(r.ids)})" for r in published
            )
            grounding.attest(record, tags=["mnemonik-blogger", "published"])

    return results
