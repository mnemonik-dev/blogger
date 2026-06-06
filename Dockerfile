# Container image for the Mnemonik blogger agent.
# Secrets are NOT baked in — inject at runtime via env / secret manager.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MNEMONIK_DRY_RUN=true

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir ".[twitter]"

# Run as non-root.
RUN useradd --create-home --uid 10001 blogger
USER blogger

ENTRYPOINT ["mnemonik-blogger"]
CMD ["platforms"]
