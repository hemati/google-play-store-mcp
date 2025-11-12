# syntax=docker/dockerfile:1

# Build stage installs dependencies once so that rebuilds are faster when
# only application code changes.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies required by google-api-python-client.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

# Runtime image
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOOGLE_SERVICE_ACCOUNT_JSON=/secrets/service_account.json \
    MCP_TRANSPORT=sse \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

COPY --from=base /usr/local /usr/local
COPY --from=base /app/src ./src

EXPOSE 8000

ENTRYPOINT ["python", "-m", "googleplay_mcp"]
