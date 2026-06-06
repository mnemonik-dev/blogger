"""The blogger agent: ground -> generate -> render -> publish -> attest.

This is the orchestration entry point used by both the CLI and a fabric runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import Platform, Settings
from .content.generate import build_source_post, render_all
from .grounding.mnemonik import Grounding, default_grounding
from .models import PublishResult, SourcePost
from .publish import build_publisher


@dataclass
class CampaignResult:
    post: SourcePost
    results: list[PublishResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    def summary(self) -> str:
        lines = [f"# {self.post.title}"]
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
    rendered = render_all(post, platforms)

    results: list[PublishResult] = []
    for platform in platforms:
        publisher = build_publisher(platform, settings)
        results.append(publisher.publish(rendered[platform]))

    if attest and not settings.dry_run:
        published = [r for r in results if r.ok and not r.dry_run]
        if published:
            record = f"Published '{title}' to: " + ", ".join(
                f"{r.platform.value} ({r.primary_url or ', '.join(r.ids)})" for r in published
            )
            grounding.attest(record, tags=["mnemonik-blogger", "published"])

    return CampaignResult(post=post, results=results)
