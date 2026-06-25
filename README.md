# Scry
[![License: BUSL-1.1](https://img.shields.io/badge/license-BUSL--1.1-blue)](LICENSE)

**Self-hosted, provenance-first data acquisition. Every fetch is an immutable, auditable artifact.**

Most scraping tools throw the raw fetch away — you get data out, but no record of exactly what was seen or when. Scry keeps it: it acquires data from the web, browsers, APIs, and files, captures an immutable, timestamped artifact of every fetch, extracts structured records with deterministic rules, and delivers them downstream. It runs in your own stack and is built to be driven by agents.

The source-available core is here: the generic engine (`fetch → parse → normalize → validate → output`), the immutable provenance store, and the CLI. Tuned source adapters, enrichment/fusion, and anti-bot logic are intentionally not part of this core. See [`docs/`](docs/).

## Features

- **Provenance-first.** Every fetch is a new immutable, timestamped, checksummed artifact. Replay any fetch to prove exactly what was seen, and diff it against a prior capture. Scry never overwrites.
- **Deterministic extraction.** CSS selectors, JSON paths, and field maps — auditable and reproducible. No black-box ML guessing.
- **Pluggable fetchers.** `web` (httpx), `browser` (Playwright), `api`, and `file`, over a common interface.
- **Self-hosted.** Runs in your own Docker stack. Your data never leaves it.
- **Agent-native.** Exposes acquisition as MCP tools, so agents acquire data with full provenance.
- **Built-in pipeline.** `fetch → parse → normalize → validate → output`, with failed records routed to a dead-letter path instead of vanishing.
- **Scheduling and queue.** Cron triggers and a dependency-free, file-backed work queue for recurring acquisition (no external broker required).

## Requirements

- Python 3.11+
- Playwright (optional — for the `browser` fetcher: `pip install 'scry[browser]'`)
- openpyxl / pdfplumber (optional — for XLSX/PDF parsing: `pip install 'scry[files]'`)

## Install

```bash
uv add scry
```

```bash
pip install scry
```

From source:

```bash
git clone https://github.com/Diwata-Domains/Scry
cd Scry
uv sync
```

## Quick start

1. Define a source — what to acquire, how, and how to extract it:

   ```yaml
   # sources/example.yaml
   name: example-articles
   fetch:
     mode: web
     url: https://example.com/articles
   parse:
     mode: html
     records: "article.post"
     fields:
       title: "h2::text"
       url: "a::attr(href)"
   ```

2. Run it:

   ```bash
   scry run sources/example.yaml
   ```

3. List the immutable artifact and the normalized records it produced:

   ```bash
   scry artifacts list
   ```

4. Replay the exact fetch to prove what was seen — and diff two captures:

   ```bash
   scry replay <artifact-id>
   scry replay --diff <artifact-id-a> <artifact-id-b>
   ```

## MCP

Scry exposes acquisition as MCP tools — submit a job, fetch a source, list artifacts — so an agent can acquire data with full provenance. Start the MCP server:

```bash
scry mcp
```

## Scheduling & workers

Add a `schedule:` (cron) to a source, then run the scheduler and a worker — no external broker needed (a local, file-backed queue):

```bash
scry scheduler --sources sources/   # enqueue sources whose cron is due
scry worker --sources sources/      # claim and run queued jobs
```

## Architecture

Scry is the Bronze layer of a Bronze → Silver → Gold lakehouse: it owns raw acquisition; normalized entities and product query surfaces live downstream. Extraction is deterministic and rule-based; ML-assisted extraction is an optional future layer. See [`docs/landscape.md`](docs/landscape.md) for the full competitive and inspirational landscape.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy scry
```

## License

[BUSL-1.1](LICENSE) (Business Source License 1.1) — source-available, converting to Apache-2.0 after the Change Date. The Additional Use Grant permits broad use but does not permit offering Scry as a competing hosted service. Commercial or hosted-use licensing: licensing@diwata.domains · Security: security@diwata.domains ([`SECURITY.md`](SECURITY.md))
