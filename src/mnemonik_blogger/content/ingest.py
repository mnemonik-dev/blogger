"""Ingest a finished article (Markdown + optional YAML front-matter) into a SourcePost.

claude-blog produces articles as Markdown files, optionally led by a YAML
front-matter block delimited by ``---``. This module turns such a file into the
blogger's canonical :class:`SourcePost` so the publish pipeline can repurpose it
per platform.

Resolution rules:
  * title   - front-matter ``title``; else the first H1; else the file stem.
  * summary - front-matter ``summary``/``description``; else the first paragraph.
  * tags    - front-matter ``tags`` (list or comma string).
  * link    - front-matter ``link``/``canonical``/``url``.

The article is treated as already-written and reviewed, so its body is not
re-grounded or mutated; only banned-phrase guardrails are enforced.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from ..models import SourcePost
from .generate import enforce_guardrails

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    parsed = yaml.safe_load(match.group(1))
    meta: dict[str, Any] = parsed if isinstance(parsed, dict) else {}
    return meta, text[match.end() :]


def _first_paragraph(body: str) -> str:
    for block in body.split("\n\n"):
        stripped = block.strip()
        if stripped and not stripped.startswith("#"):
            return " ".join(stripped.split())
    return ""


def _coerce_tags(raw: Any) -> list[str]:
    if isinstance(raw, str):
        parts = raw.split(",")
    elif isinstance(raw, list):
        parts = [str(t) for t in raw]
    else:
        return []
    return [t.strip() for t in parts if t.strip()]


def ingest_article(path: str | Path) -> SourcePost:
    """Parse a Markdown article file into a SourcePost (raises on guardrail violation)."""
    path = Path(path)
    meta, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    body = body.strip()

    fm_title = meta.get("title")
    if fm_title:
        title = str(fm_title)
    else:
        h1 = _H1.search(body)
        title = h1.group(1).strip() if h1 else path.stem
        # Drop the leading H1 so it isn't duplicated in the social copy.
        body = _H1.sub("", body, count=1).strip()

    summary = meta.get("summary") or meta.get("description") or _first_paragraph(body)
    link = meta.get("link") or meta.get("canonical") or meta.get("url")

    enforce_guardrails(f"{title} {body}")

    return SourcePost(
        title=title,
        body=body,
        summary=str(summary)[:200],
        tags=_coerce_tags(meta.get("tags")),
        link=str(link) if link else None,
    )
