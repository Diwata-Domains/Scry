# Scry — Landscape

**Status:** CANONICAL
**Lives in:** `products/scry/docs/canonical/`
**Phase:** Phase 22 — Scry
**Approved:** 2026-06-02

---

## Competitors

### Apify
Hosted scraping platform built around "actors" — isolated, containerized scraper units that run on Apify's cloud. Large actor marketplace, solid anti-bot tooling, and a managed proxy network. Cloud-first: compute is metered, data storage is on their platform, and actors run on their infra.

**How Scry differs:** Self-hosted, provenance-first, and Grain-native. Scry runs in your Docker stack alongside DAEMON, Lore, and Vault. Every job writes an immutable artifact to Vault and a normalized record to Lore. Dead jobs surface as Grain task packets. None of that maps to the Apify model.

### Scrapy
Python web scraping framework. The reference implementation for the fetch→parse→output pipeline model. OSS, battle-tested, widely used. But: no built-in scheduling (you add cron separately), no Redis queue, no provenance model, no integration with anything outside itself.

**How Scry differs:** Scry's extraction pipeline directly follows Scrapy's item pipeline architecture — fetch, parse, normalize, output — but builds scheduling, queueing, Vault integration, and Lore integration into the product rather than leaving them as manual concerns. Scry is the product; Scrapy is the pattern.

### Playwright (Microsoft)
Browser automation library. Scry uses Playwright as a dependency for the `BrowserFetcher` — it is a tool, not a competitor. Listed here because it appears in the same category searches.

**How Scry differs:** Playwright is a low-level automation API. Scry is the product layer that wraps it: source definitions, rate limiting, artifact capture, retry logic, normalization, and Lore delivery. Playwright does none of that.

### Diffbot / Import.io
AI-powered hosted web extraction services. Upload a URL, get structured JSON back. Black-box ML extraction — no rules to write, but no control over what gets extracted or how. Expensive per-call pricing, no self-hosting, no provenance tracking.

**How Scry differs:** Rule-based extraction in V1 — CSS selectors, JSON paths, field mappings defined explicitly in the source definition. Deterministic, auditable, and self-hosted. V2 may add ML-assisted extraction as an optional layer.

### Apollo / Clearbit / Hunter.io
Data enrichment APIs. Structured contact and company data available via REST. Scry can ingest from these (API source type) — they are sources, not competitors. The distinction: these services provide the data; Scry is the layer that acquires, stores, and delivers it into the Diwata ecosystem.

**How Scry differs:** Scry is acquisition infrastructure. These are data vendors.

### Airbyte / Fivetran
ELT connector platforms — move data from SaaS tools (Salesforce, Hubspot, Stripe) into a data warehouse. Strong at structured, well-defined API sources with official connectors. Not designed for raw web scraping, browser automation, or the provenance model Scry requires.

**How Scry differs:** Scry is raw acquisition first — web pages, browser-rendered content, API responses as raw bytes before normalization. Airbyte assumes a clean, structured source. Scry handles the messy unstructured case and integrates with Vault's immutable artifact model.

---

## Inspirations

### Scrapy
The item pipeline model — every collected item flows through the same stages: fetch, parse, normalize, output. Scry's `runner.py` pipeline is a direct descendant of Scrapy's architecture. The key decision Scry makes differently: the pipeline is explicit and typed rather than Scrapy's open-ended item dict.

### Grain
Job and task lifecycle model. Scry's job states (`QUEUED → RUNNING → COMPLETE → FAILED → RETRYING → DEAD`) mirror Grain's task states. More directly: dead jobs on `critical=true` sources surface as Grain task packets, feeding the human review loop that Grain owns.

### Celery / RQ
Redis-backed distributed worker queues. Scry's worker model — Redis queue, configurable worker processes, APScheduler for cron triggers — draws from the Celery/RQ pattern. RQ specifically is the direct dependency: simpler than Celery, fewer moving parts, sufficient for Scry's V1 scale.

### Wayback Machine / Common Crawl
The append-only artifact model. Every fetch is a new artifact — a timestamped, immutable record of what was seen. Scry never overwrites an artifact. Dedup by checksum skips redundant writes, but the artifact history for a source is always complete and append-only.

### Bronze / Silver / Gold Lakehouse Architecture
Scry owns the Bronze layer: raw, unprocessed, faithful-to-source data written to Vault. Lore is Silver: normalized, deduplicated, structured entities. Product-specific query surfaces (Diwa Domains graph, dashboards) are Gold. Scry's responsibility ends when raw content is in Vault and normalized records are in Lore.

---

## References

- [Scrapy documentation](https://docs.scrapy.org/) — item pipeline architecture reference
- [Playwright for Python](https://playwright.dev/python/) — browser automation integration
- [APScheduler documentation](https://apscheduler.readthedocs.io/) — cron scheduling model
- [RQ (Redis Queue) documentation](https://python-rq.org/) — worker queue implementation
- [Apify actor model](https://docs.apify.com/platform/actors) — conceptual reference for isolated job units
