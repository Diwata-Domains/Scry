# Contributing to Scry

Scry is **open-core**. This repository is **Scry Core** — the generic acquisition engine: the
pipeline, fetchers, parsers, the provenance/artifact model, the source-definition schema, and the
MCP surface. Contributions to the engine are welcome.

Product-specific source adapters, enrichment and verification, anti-bot logic, and orchestration are
maintained privately by Diwata and are **out of scope** for this repo. If a change would tie Core to
a specific data source or to Diwata's internal systems, it belongs in the private edition, not here.

## In scope

- Bug fixes in the engine
- New **generic** fetchers or parsers (a new mode, not a tuned per-site adapter)
- Provenance / replay / artifact-model improvements
- Documentation, examples, and tests

## Out of scope

- Tuned per-source adapters or source catalogs (keep these private)
- Enrichment, verification, entity-fusion, or anything that consumes a specific vendor
- Anti-bot, proxy-rotation, or rate-limit-evasion logic
- Anything coupled to the maintainer's private storage, normalization, or internal infrastructure

## Development

```bash
git clone https://github.com/Diwata-Domains/Scry
cd Scry
uv sync
uv run pytest
uv run ruff check .
uv run mypy scry
```

Keep changes focused. Match the surrounding code. Tests, `ruff`, and `mypy` must pass before a pull
request is reviewed.

## Pull requests

1. Open an issue first for anything beyond a small fix, so scope is agreed before you build.
2. Write a clear, imperative commit message describing the change.
3. Sign off your commits (see below).
4. Include tests for new behavior.

## Reporting issues

Use GitHub issues for bugs and feature requests. **Do not** file security vulnerabilities as public
issues — see [`SECURITY.md`](SECURITY.md).

## Contribution license (DCO)

Scry Core is licensed under the Business Source License 1.1, which converts to Apache-2.0 after the
Change Date, and Diwata maintains a private edition under the license's Additional Use Grant. To keep
that path clean, contributions are accepted under the
[Developer Certificate of Origin](https://developercertificate.org/): sign off each commit with

```bash
git commit -s
```

By signing off, you certify you wrote the contribution (or have the right to submit it) and license
it under this repository's license and its eventual Apache-2.0 Change License. For substantial
contributions, Diwata may request a short contributor agreement.
