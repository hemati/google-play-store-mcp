# googleplay-mcp

Python **MCP** server exposing Google Play tools:

- Reviews: list reviews, reply to a review
- Reporting: query crash-rate metrics (Android vitals)
- Purchases: verify via SubscriptionsV2

## Requirements

1. Enable APIs in your GCP project:
   - **Android Publisher API**
   - **Play Developer Reporting API**
2. Create a **Service Account**, download JSON, and grant Play Console access (Users & Permissions → Invite service account).
3. Provide credentials via one of:
   - `GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service_account.json`
   - `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT='{"type": ...}'`
   - `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=$(base64 -w0 service_account.json)`

## Install & Run (local)

```bash
conda create -n googleplay-mcp python=3.12 -y
conda activate googleplay-mcp
pip install -e .

# STDIO (local clients such as Claude Desktop)
python -m googleplay_mcp --transport stdio

# HTTP/SSE (remote clients / ChatGPT connector)
python -m googleplay_mcp --transport sse --host 0.0.0.0 --port 8000
```

### Environment variables

| Variable | Purpose |
| --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to the service account JSON credentials. |
| `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` | Raw JSON credentials string. Written to `/tmp/googleplay-service-account.json` if no path is provided. |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | Base64-encoded credentials JSON (useful for CI/CD secrets). |
| `DEFAULT_TZ` | Optional default timezone used by tools that require a timezone. |
| `MCP_TRANSPORT` | Overrides CLI transport (`stdio`, `sse`, `streamable-http`). |
| `MCP_HOST` | Host binding for HTTP transports (defaults to `0.0.0.0`). |
| `MCP_PORT` | Port for HTTP transports (defaults to FastMCP's `8000`). |
| `MCP_PATH` | Custom endpoint path when using HTTP/SSE. |
| `MCP_LOG_LEVEL` | Optional log level override passed to FastMCP. |
| `MCP_CLI_LOG_LEVEL` | Log level used by the CLI bootstrap logging (defaults to `INFO`). |
| `MCP_STATELESS_HTTP` | Set to `true` to enable stateless HTTP mode. |
| `MCP_SHOW_BANNER` | Set to `false` to hide the FastMCP startup banner. |

### Docker

Build and run the container locally (ensure the service account file exists):

```bash
docker build -t googleplay-mcp .
docker run -p 8000:8000 \
  -e GOOGLE_SERVICE_ACCOUNT_JSON=/secrets/service_account.json \
  -v $(pwd)/secrets/service_account.json:/secrets/service_account.json:ro \
  googleplay-mcp
```

The default container command exposes the server over SSE on port `8000`. To
use different transports or ports, override the environment variables at run
time, for example `-e MCP_TRANSPORT=streamable-http` or `-e MCP_PORT=9000`.

### Docker Compose

```bash
docker compose up --build
```

The included `compose.yaml` mounts `./secrets/service_account.json` into the
container and publishes the server on `http://localhost:8000/sse`.

## Tools

### `list_reviews`

* Calls Android Publisher `reviews.list`.
* Input: `package_name`, `max_results`, optional `translation_language`.

### `reply_to_review`

* Calls Android Publisher `reviews.reply`.

### `crash_rate`

* Calls Reporting API `vitals.crashrate.query` (DAILY aggregation, tz-aware).

### `get_subscription_v2`

* Calls Android Publisher `purchases.subscriptionsv2.get`.

## Using from ChatGPT / MCP Clients

* Local (STDIO): use `mcp.config.example.json` with a client that supports STDIO (e.g., Claude Desktop).
* Remote (HTTP/SSE): expose the container behind HTTPS and register it as a custom connector in ChatGPT Agent Builder or ChatGPT Playground. The SSE endpoint defaults to `https://<your-domain>/sse` and expects POSTs to `https://<your-domain>/messages/`.

## Notes

* Docstrings are in English for better LLM usability.
* Add retries (`tenacity`) and caching for Reporting API as needed.

---

## Next Steps

* Add more tools (ANR rate, wake-up, releases, etc.).
* Wrap long-running calls with retries/timeouts.
* Add CI.
