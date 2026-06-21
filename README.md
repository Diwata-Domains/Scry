# Scry

**Self-hosted, provenance-first data acquisition for the Diwata stack.**

Scry is Diwata's ingestion layer: it acquires raw data from the web, browsers, APIs, and files,
captures an immutable artifact of exactly what was seen, normalizes it, and delivers structured
records downstream. It is the **Bronze layer** of a Bronze → Silver → Gold lakehouse — Scry owns
raw acquisition; Lore owns normalized entities; product surfaces (the Diwa Domains graph) own the
Gold query layer.

> **Status:** v0.1.0 · Phase 1 (fetcher foundation). Canonical design approved 2026-06-02.
> This repository is the public face of Scry — architecture, design, and provenance model. The
> production implementation is developed and maintained by Diwata LLC as part of the Diwata stack.

---

## What it does

```
source definition → fetch → parse → normalize → validate → output
                       │                                       │
                       ▼                                       ▼
                immutable artifact (Vault)            normalized record (Lore)
```

- **Fetch** — pluggable fetchers per acquisition mode: `web` (httpx), `browser` (Playwright for
  rendered content), `api` (REST), `file`.
- **Parse** — rule-based, deterministic extraction: `html` (CSS selectors), `json_path`, `file`.
- **Normalize / validate** — map extracted fields to a typed canonical shape; failed records go to
  a dead-letter path with error metadata rather than vanishing.
- **Output** — write the raw artifact to Vault (append-only, deduplicated by checksum) and the
  normalized record to Lore.
- **Schedule / queue / worker** — Redis/RQ job queue, APScheduler cron triggers, configurable
  worker processes. Job lifecycle: `QUEUED → RUNNING → COMPLETE → FAILED → RETRYING → DEAD`.
- **MCP** — exposes acquisition as MCP tools so agents can invoke it.

## Design principles

- **Provenance first.** Every fetch is a new, timestamped, immutable artifact. Scry never
  overwrites — the artifact history for a source is always complete and append-only (modeled on the
  Wayback Machine / Common Crawl approach).
- **Self-hosted.** Runs in your own Docker stack. No third-party cloud holds the data.
- **Deterministic extraction.** V1 extraction is explicit rules (selectors, JSON paths, field
  maps) — auditable and reproducible. ML-assisted extraction is a possible optional V2 layer.

## Architecture

See [`docs/landscape.md`](docs/landscape.md) for the full competitive and inspirational landscape —
how Scry relates to Scrapy, Playwright, Apify, Airbyte/Fivetran, and the Bronze/Silver/Gold
lakehouse model.

## Ownership & license

Scry is a product of **Diwata LLC**. This repository is published for transparency and reference.
It is **source-visible, all rights reserved** — see [`NOTICE.md`](NOTICE.md). A formal open-source
or source-available license may be applied to a designated core in the future. For commercial use
or licensing, contact Diwata LLC.
