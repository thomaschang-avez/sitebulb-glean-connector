# Sitebulb Glean Connector

Monthly SEO pipeline that pulls Sitebulb Historical Hint Data from Google Sheets for each client, diffs it against the previous run, sends a Slack alert with new and resolved issues, and indexes the results into Glean enterprise search for AI-assisted analysis.

## Architecture

```
Google Sheets (Sitebulb Historical Hint Data export per client)
  → parser.py       Parse hint rows, score by severity
  → diff.py         Compare latest vs previous snapshot
  → slack_alert.py  Post summary: new issues, resolved, score delta
  → glean_push.py   Index structured audit data into Glean
```

## What it tracks

29 SEO hint types mapped to severity scores and categories:

| Category | Examples |
|---|---|
| Crawlability | Broken internal URLs, orphaned pages, redirect loops |
| Indexability | Canonical mismatches, noindex conflicts |
| On-Page SEO | Missing titles, duplicate H1s, empty meta descriptions |
| Performance | High TTFB, render-blocking resources |
| Mobile SEO | Missing viewport meta tag |
| Content Quality | Lorem ipsum dummy text |
| Security | Password fields over HTTP |

**Severity scoring:** Critical (100) · High (75) · Medium (50) · Low (25)

## Slack alert format

For each client, posts a message with:
- Total score and delta vs previous run
- New issues (by severity)
- Resolved issues
- Unchanged critical/high issues still open

## Glean indexing

Each audit is indexed as a structured Glean document, making the full issue history searchable and available to AI tools that query the enterprise knowledge graph.

## Setup

```bash
cp .env.example .env
# Fill in Glean, Slack, and Google credentials
pip install -r requirements.txt
```

### Google Sheets format

Each client needs a Google Sheet with Sitebulb Historical Hint Data export. In Sitebulb: **Export → Historical Hint Data → CSV**, then upload to Google Sheets. Set the Sheet ID in `config.py`.

### Run

```bash
# Single client
python3 main.py --client "Client A"

# All clients
python3 main.py

# Dry run (parse only, no Slack/Glean)
python3 main.py --dry-run
```

## Files

| File | Purpose |
|---|---|
| `config.py` | Client list, hint severity mapping, env var loading |
| `parser.py` | Reads Google Sheets, maps hint rows to structured data |
| `diff.py` | Compares current run to previous snapshot |
| `slack_alert.py` | Formats and posts Slack summary per client |
| `glean_push.py` | Indexes audit results into Glean |
| `main.py` | Entry point — orchestrates the full pipeline |
