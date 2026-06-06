# Deployment (enterprise-style)

The agent is stateless and credential-driven. Nothing is hardcoded; every secret
is injected at runtime. Two supported delivery shapes:

## 1. Container (any orchestrator)

```bash
docker build -t mnemonik-blogger .
docker run --rm \
  -e MNEMONIK_DRY_RUN=false \
  -e TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  -e TELEGRAM_CHANNEL=@mnemonik \
  -e DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL" \
  -e X_API_KEY="$X_API_KEY" -e X_API_SECRET="$X_API_SECRET" \
  -e X_ACCESS_TOKEN="$X_ACCESS_TOKEN" -e X_ACCESS_TOKEN_SECRET="$X_ACCESS_TOKEN_SECRET" \
  -e FARCASTER_NEYNAR_API_KEY="$FARCASTER_NEYNAR_API_KEY" \
  -e FARCASTER_SIGNER_UUID="$FARCASTER_SIGNER_UUID" \
  mnemonik-blogger post --title "..." --brief "..." --platforms auto --live
```

## 2. Fabric runner (coding-fabric / agent-fabric)

> TODO: confirm the exact `coding-fabric` contract (job spec, secret-mount path,
> entrypoint convention). This repo is structured so the fabric only needs to:
>   1. provide the platform secrets as environment variables (or mount them and
>      export before invoking), and
>   2. call `mnemonik-blogger post ... --live`.
>
> Add the fabric job manifest here once the contract is confirmed. See the
> session notes: `mnemonik-dev/coding-fabric` was out of this session's repo
> scope, so the manifest is a placeholder.

## Secret management rules

- Never commit `.env` or `facts.yaml` (gitignored).
- Secrets are read as `SecretStr` and never logged.
- Default is dry-run; publishing requires an explicit `--live` or
  `MNEMONIK_DRY_RUN=false`.
- Rotate platform tokens via the secret manager, not in code.
