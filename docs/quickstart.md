# Quickstart

A five-minute tour of Scry: acquire a source, inspect the immutable artifact, and replay it to prove
exactly what was fetched.

## 1. Install

```bash
uv add scry
```

Start Redis (the job queue) if it is not already running:

```bash
docker run -p 6379:6379 redis
```

## 2. Define a source

A source declares what to acquire, how to fetch it, and how to extract structured records. Extraction
is deterministic — explicit selectors and field maps, no ML guessing.

```yaml
# sources/articles.yaml
name: example-articles
fetch:
  mode: web              # web | browser | api | file
  url: https://example.com/articles
parse:
  mode: html             # html | json_path | file
  records: "article.post"
  fields:
    title: "h2::text"
    url: "a::attr(href)"
    published: "time::attr(datetime)"
```

## 3. Run it

```bash
scry run sources/articles.yaml
```

Scry fetches the source, writes an **immutable artifact** of the raw response (timestamped and
checksummed), then parses, normalizes, validates, and emits structured records. Records that fail
validation are routed to a dead-letter path with error metadata rather than dropped.

## 4. Inspect the artifact

```bash
scry artifacts list
```

Each artifact records what was fetched, when, and a checksum of the exact bytes seen. Artifacts are
append-only — Scry never overwrites a prior capture, so the history of a source is always complete.

## 5. Replay and diff

This is the point of provenance: prove what was seen, and see what changed between captures.

```bash
scry replay <artifact-id>
scry replay --diff <artifact-id-a> <artifact-id-b>
```

## 6. Schedule it

Add a schedule to acquire on a cron cadence; Redis-backed workers run the jobs.

```yaml
schedule: "0 * * * *"    # hourly
```

```bash
scry worker        # run a worker
scry scheduler     # run the scheduler
```

## 7. Drive it from an agent

Scry exposes acquisition as MCP tools, so an agent can submit jobs, fetch sources, and list artifacts
with full provenance.

```bash
scry mcp
```

## Next

- [`README.md`](../README.md) — features and overview
- [`docs/landscape.md`](landscape.md) — how Scry relates to Scrapy, Webrecorder, Firecrawl, Airbyte, and the lakehouse model
