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


class ToSClass(str, Enum):
    """How a capture may be used downstream — recorded on the source, the artifact,
    and every normalized record, so a consumer can gate mechanically rather than by
    memory. (A hosted/SaaS surface should refuse anything not clearly clean.)
    """

    CLEAN_PUBLIC = "clean_public"
    """Unauthenticated, public data (open API, RSS, a public web page)."""

    CLEAN_USER_SESSION = "clean_user_session"
    """The end user's OWN authenticated session, user-triggered (e.g. a browser
    extension capturing a page the user is already viewing). Defensible to surface."""

    RESTRICTED_INTERNAL = "restricted_internal"
    """Anything relying on operator-side login, scale, or evasion. Internal / private
    use only — never surface in a product offered to third parties."""


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
    tos_class: ToSClass = ToSClass.CLEAN_PUBLIC  # how captures may be used downstream


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
    tos_class: str = ToSClass.CLEAN_PUBLIC.value  # inherited from the source; gate on this
