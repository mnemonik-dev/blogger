"""Build a grounded SourcePost from a brief and render it for each platform.

`build_source_post` assembles a canonical post from a short brief plus grounded
protocol facts. It is deterministic (no LLM) so the pipeline is testable and
reproducible; the agent runtime can override `body`/`summary` with LLM-written
copy while keeping the same grounding and guardrails.
"""

from __future__ import annotations

from ..config import Platform
from ..grounding.mnemonik import Grounding, StaticGrounding
from ..models import RenderedPost, SourcePost
from . import formatters, voice


def _enforce_guardrails(text: str) -> None:
    lowered = text.lower()
    for banned in voice.BANNED_PHRASES:
        if banned in lowered:
            raise ValueError(f"Guardrail violation: banned phrase {banned!r} in content")


def build_source_post(
    *,
    title: str,
    brief: str,
    link: str | None = None,
    tags: list[str] | None = None,
    grounding: Grounding | None = None,
    fact_query: str | None = None,
    summary: str | None = None,
) -> SourcePost:
    """Assemble a canonical, grounded post.

    `brief` is the human-supplied angle/body. Facts are pulled from `grounding`
    and woven in as a short "why it matters" close so claims stay sourced.
    """
    grounding = grounding or StaticGrounding()
    facts = grounding.recall(fact_query or title, limit=3)

    body = brief.strip()
    if facts:
        proof = " ".join(f.text for f in facts[:2])
        body = f"{body}\n\nWhy it holds up: {proof}"

    _enforce_guardrails(title + " " + body)

    return SourcePost(
        title=title,
        body=body,
        summary=(summary or brief.strip().split("\n", 1)[0])[:200],
        tags=tags or voice.HASHTAGS[:3],
        link=link,
        facts=facts,
    )


def render_all(post: SourcePost, platforms: list[Platform]) -> dict[Platform, RenderedPost]:
    return {p: formatters.render(p, post) for p in platforms}
