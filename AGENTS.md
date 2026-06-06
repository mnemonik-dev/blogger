# AGENTS.md

Mnemonik blogger agent — content generation + multi-platform publishing.

## What this is

A standalone agent that turns a brief about the Mnemonik protocol into
platform-native posts and publishes them to **Telegram, Discord, X, and
Farcaster**. Posts are grounded in protocol facts (ideally pulled live from the
Mnemonik MCP) and, when publishing for real, the agent records a verifiable
attestation of what went out.

## Layout

- `src/mnemonik_blogger/config.py` — env-driven settings; secrets as `SecretStr`.
- `src/mnemonik_blogger/content/` — voice rules, formatters (per-platform length
  + thread splitting), and grounded post assembly.
- `src/mnemonik_blogger/grounding/mnemonik.py` — `Grounding` protocol; static /
  file fallbacks; wire the live Mnemonik MCP here.
- `src/mnemonik_blogger/publish/` — one adapter per platform + a registry.
- `src/mnemonik_blogger/agent.py` — ground → generate → render → publish → attest;
  plus `run_campaign_from_article` (ingest → quality gate → publish).
- `src/mnemonik_blogger/content/ingest.py` — parse a finished Markdown article
  (front-matter + body) into a `SourcePost`.
- `src/mnemonik_blogger/quality.py` — score an article via claude-blog's
  `analyze_blog.py` and gate publishing on `score.total >= min_score`. Fails closed.
- `src/mnemonik_blogger/cli.py` — `platforms`, `preview`, `post` (`--from-file`), `score`.

## Write → gate → publish

For finished articles (e.g. written by claude-blog), publishing is **quality-gated**:

```bash
# Score only (no publish); exits non-zero below threshold.
MNEMONIK_CLAUDE_BLOG_PATH=../claude-blog mnemonik-blogger score article.md

# Publish only if score.total >= min_score (default 80); dry-run unless --live.
MNEMONIK_CLAUDE_BLOG_PATH=../claude-blog \
  mnemonik-blogger post --from-file article.md --platforms auto
```

The gate **fails closed**: if `MNEMONIK_CLAUDE_BLOG_PATH` is unset or the analyzer
errors, the article is blocked and nothing publishes.

## Rules

- Python 3.11+. Keep secrets out of code and logs.
- Default to dry-run; real posting requires `--live` / `MNEMONIK_DRY_RUN=false`.
- Every protocol claim must trace to a grounded fact (see `content/voice.py`
  guardrails).
- Run checks before handoff:

```bash
ruff check .
ruff format --check .
mypy
pytest -q
```

## Open items

- Wire the live Mnemonik MCP into `Grounding` (recall + sign_memory).
- Confirm the `coding-fabric` job contract and add the deploy manifest
  (`deploy/`).
- Confirm official Mnemonik BRAND/VOICE and replace the provisional defaults.
