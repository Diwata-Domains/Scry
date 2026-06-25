# Scry — Landscape

How Scry relates to the tools it's often compared to, and the ideas it builds on.

Scry's lane: **provenance-first, deterministic, self-hosted, agent-native** acquisition — reproducible data collection you can audit. It runs entirely in your own stack with no external broker, and every fetch is an immutable, replayable artifact.

---

## Competitors

### Apify
Hosted scraping platform built around containerized "actors" that run on Apify's cloud, with an actor marketplace, anti-bot tooling, and a managed proxy network. Cloud-first: compute is metered and your data lives on their platform.

**How Scry differs:** self-hosted and provenance-first. Scry runs in your own environment; every fetch writes an immutable, timestamped, checksummed artifact you can `replay` and `diff`. Your data never leaves your stack.

### Scrapy
The reference Python web-scraping framework and the lineage for the fetch→parse→output pipeline model. Battle-tested, but it leaves scheduling, queueing, and provenance as concerns you wire up yourself.

**How Scry differs:** Scry follows Scrapy's item-pipeline shape (fetch → parse → normalize → validate → output) but ships scheduling (a dependency-free cron matcher), a file-backed work queue, and an immutable provenance/replay model as part of the engine. Scry is the product; Scrapy is the pattern.

### Playwright
A browser-automation library — a dependency Scry uses for the optional `browser` fetcher, not a competitor.

**How Scry differs:** Playwright is a low-level automation API; Scry is the layer above it — declarative source definitions, rate limiting, artifact capture, retry logic, and deterministic extraction.

### Firecrawl / Crawl4AI / Jina Reader
"LLM-ready" web extraction — fast, convenient, increasingly the default for agent pipelines. But extraction is non-deterministic and the raw fetch is not preserved as an auditable record.

**How Scry differs:** deterministic, rule-based extraction (CSS selectors, JSON paths, field maps) plus a provenance artifact of exactly what was fetched. Counter-position: *extraction you can audit and reproduce*, not a black box.

### Diffbot / Import.io
AI-powered hosted extraction — give a URL, get JSON. No rules to write, but no control over what's extracted, hosted-only, no provenance.

**How Scry differs:** explicit, deterministic rules in V1; self-hosted; every fetch is a replayable artifact. ML-assisted extraction is a possible optional layer later, never the only path.

### Enrichment APIs (PDL, Hunter, Clearbit, etc.)
Structured contact/company data via REST. These are **sources** Scry can ingest from (the `api` source type), not competitors — they provide data; Scry acquires, records, and delivers it with provenance.

### Airbyte / Fivetran
ELT connector platforms that move data from well-defined SaaS APIs into a warehouse. Strong on structured, official-connector sources; not built for raw web/browser acquisition or a provenance model.

**How Scry differs:** Scry is raw-acquisition-first — web pages, browser-rendered content, and API responses captured as immutable bytes before normalization. It handles the messy, unstructured case and keeps the audit trail.

### Webrecorder / Browsertrix (WARC)
The closest in *spirit* — capture-and-replay web archiving built on the WARC standard. Aimed at archiving rather than structured pipelines.

**How Scry differs:** Scry pairs provenance/replay with a structured extraction pipeline and an agent-facing surface. Align with WARC, don't collide with it.

---

## Inspirations

### Scrapy — the item pipeline
Every collected record flows through the same explicit, typed stages: fetch → parse → normalize → validate → output. Scry's runner is a direct descendant; the difference is an explicit typed pipeline rather than an open-ended item dict.

### Wayback Machine / Common Crawl / WARC — the append-only artifact
Every fetch is a new, timestamped, immutable artifact; Scry never overwrites. Content is content-addressed (SHA-256) and deduplicated, but the capture history for a source is always complete and append-only — so you can prove exactly what was seen and diff captures over time.

### Medallion (Bronze layer)
Scry deliberately owns only **raw acquisition** — faithful-to-source bytes plus a provenance record. Normalization into structured entities and any query/serving layer are downstream concerns left to the consumer; Scry's responsibility ends when the raw artifact and the normalized records are produced.

---

## Design choices worth noting

- **No external broker.** The work queue is a dependency-free, file-backed queue and the scheduler is a small built-in cron matcher — Scry runs with nothing but Python and your sources. (Heavier backends can implement the same queue interface if you need them.)
- **Agent-native.** Acquisition is exposed as MCP tools, so an agent can submit jobs, list artifacts, and replay captures with provenance carried through.

---

## References

- [Scrapy documentation](https://docs.scrapy.org/) — item-pipeline architecture
- [Playwright for Python](https://playwright.dev/python/) — browser automation
- [WARC / Webrecorder](https://webrecorder.net/) — web-archive capture & replay
- [Apify actor model](https://docs.apify.com/platform/actors) — isolated job units
- [Firecrawl](https://www.firecrawl.dev/) — LLM-oriented web extraction (contrast)
