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
3. Set `GOOGLE_SERVICE_ACCOUNT_JSON` env var to the JSON path.

## Install & Run (local)

```bash
uv venv || python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env  # optional
./scripts/run_stdio.sh
````

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

* Local (STDIO): use `mcp.config.example.json` with a client that supports STDIO.
* Remote (HTTP/SSE): deploy the server behind HTTPS and register as a **custom connector** in ChatGPT (Deep Research). See linked docs.

## Notes

* Docstrings are in English for better LLM usability.
* Add retries (`tenacity`) and caching for Reporting API as needed.

---

## Next Steps

* Add more tools (ANR rate, wake-up, releases, etc.).
* Wrap long-running calls with retries/timeouts.
* Add Dockerfile + CI as needed.
