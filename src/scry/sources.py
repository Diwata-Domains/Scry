"""Source-definition loading — the documented YAML format.

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
    output_schema: { entity_type: article, required: [title] }
    schedule: "0 * * * *"    # optional cron
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scry.models import SourceDefinition

_VALID_TYPES = {"web", "api", "file", "browser"}
_DEFAULT_PARSER = {"web": "html", "browser": "html", "api": "json_path", "file": "file"}


def source_from_dict(data: dict[str, Any], *, source_id: str | None = None) -> SourceDefinition:
    name = data.get("name") or source_id
    if not name:
        raise ValueError("source definition requires a 'name'")
    fetch = data.get("fetch") or {}
    parse = data.get("parse") or {}
    mode = fetch.get("mode")
    if mode not in _VALID_TYPES:
        raise ValueError(f"fetch.mode must be one of {sorted(_VALID_TYPES)}, got {mode!r}")

    extraction_rules: dict[str, Any] = {}
    if "records" in parse:
        extraction_rules["records"] = parse["records"]
    if "fields" in parse:
        extraction_rules["fields"] = parse["fields"]
    if "file_type" in parse:
        extraction_rules["file_type"] = parse["file_type"]

    return SourceDefinition(
        id=name,
        name=name,
        source_type=mode,
        parser=parse.get("mode") or _DEFAULT_PARSER[mode],
        url=fetch.get("url"),
        auth_config=fetch.get("auth"),
        extraction_rules=extraction_rules,
        output_schema=data.get("output_schema"),
        rate_limit=fetch.get("rate_limit"),
        schedule=data.get("schedule"),
        critical=data.get("critical", False),
        enabled=data.get("enabled", True),
    )


def load_source(path: str | Path) -> SourceDefinition:
    """Load one source definition from a YAML file."""
    import yaml

    p = Path(path)
    data = yaml.safe_load(p.read_text()) or {}
    return source_from_dict(data, source_id=p.stem)


def load_sources(directory: str | Path) -> list[SourceDefinition]:
    """Load every *.yaml / *.yml source definition in a directory."""
    d = Path(directory)
    files = sorted([*d.glob("*.yaml"), *d.glob("*.yml")])
    return [load_source(f) for f in files]
