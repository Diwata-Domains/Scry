"""Scry — provenance-first acquisition engine.

The generic, source-available core: fetch -> parse -> normalize -> validate -> output,
where every fetch is captured as an immutable, checksummed, replayable artifact.

This package is the generic engine only. Tuned source adapters, enrichment/fusion,
anti-bot logic, and product-specific wiring are not part of it.
"""

from scry.auth import AuthenticatedFetcher
from scry.health import HealthReport, RunLog, evaluate
from scry.models import (
    FetchResult,
    JobStatus,
    NormalizedRecord,
    ParsedRecord,
    SourceDefinition,
    ToSClass,
)
from scry.provenance import Artifact, ArtifactStore
from scry.runner import RunResult, run_source
from scry.sources import load_source, load_sources

__version__ = "0.2.1"

__all__ = [
    "FetchResult",
    "JobStatus",
    "NormalizedRecord",
    "ParsedRecord",
    "SourceDefinition",
    "Artifact",
    "ArtifactStore",
    "AuthenticatedFetcher",
    "ToSClass",
    "RunResult",
    "run_source",
    "evaluate",
    "HealthReport",
    "RunLog",
    "load_source",
    "load_sources",
    "__version__",
]
