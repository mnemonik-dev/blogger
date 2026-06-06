"""Command-line interface.

    mnemonik-blogger platforms                 # show which platforms are credential-ready
    mnemonik-blogger preview --title ... --brief ...   # render without posting
    mnemonik-blogger post --title ... --brief ... --platforms telegram,x

By default everything runs in dry-run (MNEMONIK_DRY_RUN=true). Pass --live to
actually publish (requires credentials in the environment).
"""

from __future__ import annotations

import typer

from .agent import run_campaign
from .config import Platform, Settings, load_settings
from .content.formatters import render
from .content.generate import build_source_post
from .grounding.mnemonik import default_grounding

app = typer.Typer(add_completion=False, help="Mnemonik multi-platform blogger agent.")


def _parse_platforms(value: str | None, settings: Settings) -> list[Platform]:
    if not value or value == "auto":
        ready = settings.configured_platforms()
        return ready or list(Platform)
    aliases = {"x": Platform.TWITTER, "tg": Platform.TELEGRAM}
    out: list[Platform] = []
    for raw in (p.strip().lower() for p in value.split(",") if p.strip()):
        out.append(aliases[raw] if raw in aliases else Platform(raw))
    return out


@app.command()
def platforms() -> None:
    """List platforms and whether their credentials are configured."""
    settings = load_settings()
    ready = set(settings.configured_platforms())
    typer.echo(f"dry_run = {settings.dry_run}")
    for p in Platform:
        mark = "ready" if p in ready else "missing credentials"
        typer.echo(f"  {p.value:10} {mark}")


@app.command()
def preview(
    title: str = typer.Option(..., help="Post title."),
    brief: str = typer.Option(..., help="The angle / body of the post."),
    link: str = typer.Option(None, help="Canonical URL to include."),
    tags: str = typer.Option(None, help="Comma-separated hashtags."),
    target: str = typer.Option("auto", "--platforms", help="Comma list or 'auto'."),
) -> None:
    """Render platform-native variants without publishing."""
    settings = load_settings()
    chosen = _parse_platforms(target, settings)
    post = build_source_post(
        title=title,
        brief=brief,
        link=link,
        tags=[t.strip() for t in tags.split(",")] if tags else None,
        grounding=default_grounding(settings.facts_path),
    )
    for platform in chosen:
        rendered = render(platform, post)
        typer.echo(f"\n===== {platform.value} ({len(rendered.segments)} segment(s)) =====")
        for i, seg in enumerate(rendered.segments, 1):
            typer.echo(f"--- {i} ---\n{seg}")


@app.command()
def post(
    title: str = typer.Option(..., help="Post title."),
    brief: str = typer.Option(..., help="The angle / body of the post."),
    link: str = typer.Option(None, help="Canonical URL to include."),
    tags: str = typer.Option(None, help="Comma-separated hashtags."),
    target: str = typer.Option("auto", "--platforms", help="Comma list or 'auto'."),
    live: bool = typer.Option(False, "--live", help="Actually publish (overrides dry-run)."),
) -> None:
    """Generate and publish a post across platforms."""
    settings = load_settings()
    if live:
        settings.dry_run = False
    chosen = _parse_platforms(target, settings)
    result = run_campaign(
        title=title,
        brief=brief,
        link=link,
        tags=[t.strip() for t in tags.split(",")] if tags else None,
        platforms=chosen,
        settings=settings,
    )
    typer.echo(result.summary())
    if not result.ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
