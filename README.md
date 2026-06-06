# Mnemonik Blogger

A content + multi-platform publishing agent for the **Mnemonik protocol**. Give it
a brief; it produces platform-native posts, grounds every claim in protocol facts,
and publishes to **Telegram, Discord, X (Twitter), and Farcaster** — then records a
verifiable attestation of what it published.

> Mnemonik = verifiable memory for AI agents: recall it, and prove it.

## Pipeline

```
brief ─▶ ground (Mnemonik MCP / facts) ─▶ generate (voice + guardrails)
      ─▶ render per platform (length + threads) ─▶ publish (APIs) ─▶ attest
```

## Platforms

| Platform   | Transport                                   | Threads |
|------------|---------------------------------------------|---------|
| Telegram   | Bot API → channel (bot must be admin)       | yes     |
| Discord    | channel webhook (or bot token + channel id) | yes     |
| X (Twitter)| API v2 via tweepy (paid tier for write)     | yes     |
| Farcaster  | Neynar API (managed signer)                 | yes     |

## Install

```bash
pip install -e ".[dev,twitter]"      # twitter extra pulls in tweepy
cp .env.example .env                  # fill in only the platforms you use
```

## Use

```bash
# Which platforms have credentials?
mnemonik-blogger platforms

# Preview renders without posting (safe, no creds needed):
mnemonik-blogger preview \
  --title "Provable agent memory" \
  --brief "Agents forget, and you can't audit what they recalled. Mnemonik changes that." \
  --platforms auto

# Publish for real (requires credentials in env):
mnemonik-blogger post \
  --title "Provable agent memory" \
  --brief "..." \
  --link "https://mnemonik.xyz" \
  --platforms telegram,discord,x,farcaster \
  --live
```

By default the agent runs in **dry-run** (renders + reports, never posts). Real
posting requires `--live` or `MNEMONIK_DRY_RUN=false`.

## Grounding with the Mnemonik MCP

`grounding/mnemonik.py` defines a `Grounding` protocol. Out of the box it uses
built-in facts (`StaticGrounding`) or a YAML file (`FileGrounding`,
`MNEMONIK_FACTS_PATH`). To ground content in **live, attested** protocol facts and
to **sign** each publish, wire the Mnemonik MCP (`mnemonic_recall`,
`mnemonic_sign_memory`, `mnemonic_verify`) into a `Grounding` implementation — see
`.mcp.json` and `AGENTS.md`.

## Secrets & deployment

Nothing is hardcoded. Secrets are read from the environment as `SecretStr`
(never logged) and injected at deploy time by a secret manager / fabric runner.
See [`deploy/`](deploy/README.md).

## Develop

```bash
ruff check . && ruff format --check . && mypy && pytest -q
```

## Status

v0.1 scaffold. Provisional Mnemonik voice/facts (derived from the protocol's MCP
tool descriptions) — confirm against the official BRAND/VOICE. Live MCP grounding
and the `coding-fabric` deploy manifest are tracked in `AGENTS.md` open items.
