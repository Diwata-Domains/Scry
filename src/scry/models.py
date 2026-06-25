"""Core data models for the Scry pipeline (generic, no product coupling)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"


@dataclass
class SourceDefinition:
    """Declarative description of what to acquire, how, and how often.

    Loaded from a YAML file (see `scry.sources.load_source`):

        name: example-articles
        fetch:  { mode: web, url: https://... }
        parse:  { mode: html, records: "article.post", fields: { title: "h2::text" } }
        output_schema: { entity_type: article, required: [title] }
        schedule: "0 * * * *"
    """

    id: str
    name: str
    source_type: str            # fetch.mode — "web" | "api" | "file" | "browser"
    parser: str                 # parse.mode — "html" | "json_path" | "file"
    url: Optional[str] = None
    auth_config: Optional[dict[str, Any]] = None
    extraction_rules: dict[str, Any] = field(default_factory=dict)  # {records?, fields}
    output_schema: Optional[dict[str, Any]] = None
    rate_limit: Optional[dict[str, Any]] = None
    schedule: Optional[str] = None   # cron expression or None / "on_demand"
    critical: bool = False
    enabled: bool = True


@dataclass
class FetchResult:
    content: bytes
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedRecord:
    fields: dict[str, Any]


@dataclass
class NormalizedRecord:
    entity_type: str
    data: dict[str, Any]
    artifact_id: Optional[str] = None
