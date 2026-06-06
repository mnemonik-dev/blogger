from __future__ import annotations

from pathlib import Path

import pytest

from mnemonik_blogger.content.ingest import ingest_article


def test_ingest_uses_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "a.md"
    path.write_text(
        "---\n"
        "title: Provable Agent Memory\n"
        "summary: Agents forget; we make recall verifiable.\n"
        "tags: [Mnemonik, AIagents]\n"
        "link: https://mnemonik.xyz\n"
        "---\n"
        "# A Different Heading\n\nBody text here.\n",
        encoding="utf-8",
    )
    post = ingest_article(path)
    assert post.title == "Provable Agent Memory"
    assert post.summary == "Agents forget; we make recall verifiable."
    assert post.tags == ["Mnemonik", "AIagents"]
    assert post.link == "https://mnemonik.xyz"
    # Front-matter title present, so the H1 is kept in the body.
    assert "A Different Heading" in post.body


def test_ingest_falls_back_to_h1_and_first_paragraph(tmp_path: Path) -> None:
    path = tmp_path / "b.md"
    path.write_text(
        "# Verifiable Memory\n\nThe first paragraph becomes the summary.\n\nMore body.\n",
        encoding="utf-8",
    )
    post = ingest_article(path)
    assert post.title == "Verifiable Memory"
    assert post.summary == "The first paragraph becomes the summary."
    # H1 stripped from body when it was the title source.
    assert not post.body.startswith("# Verifiable Memory")
    assert "More body." in post.body


def test_ingest_comma_string_tags(tmp_path: Path) -> None:
    path = tmp_path / "c.md"
    path.write_text(
        "---\ntags: Mnemonik, Solana , Arweave\n---\n# T\n\nBody.\n",
        encoding="utf-8",
    )
    post = ingest_article(path)
    assert post.tags == ["Mnemonik", "Solana", "Arweave"]


def test_ingest_enforces_guardrails(tmp_path: Path) -> None:
    path = tmp_path / "d.md"
    path.write_text("# Buy now\n\nGuaranteed returns, 100x.\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ingest_article(path)
