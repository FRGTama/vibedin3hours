# Scraper

Scrapes articles from `support.optisigns.com` via the Zendesk Help Center API, converts them to clean Markdown, and tracks changes with SHA256 delta detection.

## Setup

```bash
cp .env.sample .env
# Fill in your Zendesk credentials in .env
pip install -r requirements.txt
```

## Run Locally

```bash
python main.py
```

Output:
```
added=30 updated=0 skipped=0
```

Articles are saved to `articles/<id>-<slug>.md`. Detected changes use SHA256 hashing tracked in `articles/state.json`.

## Run with Docker

```bash
docker build -t scraper .
docker run --rm \
  -e ZENDESK_SUBDOMAIN=your_subdomain \
  -e ZENDESK_EMAIL=your_email@example.com \
  -e ZENDESK_API_TOKEN=your_token \
  -v $(pwd)/articles:/app/articles \
  scraper
```

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `ZENDESK_SUBDOMAIN` | yes | — |
| `ZENDESK_EMAIL` | yes | — |
| `ZENDESK_API_TOKEN` | yes | — |
| `ARTICLES_DIR` | no | `articles` |
| `STATE_FILE` | no | `state.json` |
| `RATE_LIMIT_DELAY` | no | `1.0` |
| `MAX_RETRIES` | no | `3` |

## Output

| File | Purpose |
|------|---------|
| `articles/<id>-<slug>.md` | Clean Markdown article |
| `articles/state.json` | SHA256 hashes for delta detection |
