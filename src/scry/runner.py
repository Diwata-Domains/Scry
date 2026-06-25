"""Pipeline runner — fetch -> artifact (provenance) -> parse -> normalize -> validate.

Output is normalized records PLUS the artifact id, so every record is traceable
back to the exact bytes it came from.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Optional

from scry.fetchers import FETCHERS, WebFetcher
from scry.models import JobStatus, NormalizedRecord, SourceDefinition
from scry.normalize import normalize
from scry.parsers import PARSERS, HTMLParser
from scry.provenance import ArtifactStore
from scry.validate import ValidationResult, should_fail_job, validate

logger = logging.getLogger("scry")


@dataclass
class RunResult:
    source_id: str
    status: JobStatus
    artifact_id: Optional[str]
    records: list[NormalizedRecord]
    invalid: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "status": self.status.value,
            "artifact_id": self.artifact_id,
            "records": [asdict(r) for r in self.records],
            "invalid": self.invalid,
            "error": self.error,
        }


def run_source(source: SourceDefinition, store: ArtifactStore) -> RunResult:
    """Run the full pipeline for one source against a provenance store."""
    fetcher = FETCHERS.get(source.source_type, WebFetcher)()
    parser = PARSERS.get(source.parser, HTMLParser)()
    entity_type = (source.output_schema or {}).get("entity_type", "document")
    try:
        tos_class = source.tos_class.value
        fetch_result = fetcher.fetch(source)
        artifact = store.write(source.id, fetch_result, tos_class=tos_class)  # provenance before parsing
        logger.info("captured source=%s artifact=%s bytes=%d tos=%s",
                    source.id, artifact.artifact_id, artifact.size, tos_class)

        records: list[NormalizedRecord] = []
        results: list[ValidationResult] = []
        for pr in parser.parse(fetch_result.content, source.extraction_rules):
            nr = normalize(pr, entity_type)
            if not nr.data:
                continue
            nr.artifact_id = artifact.artifact_id
            nr.tos_class = tos_class  # travels with every record for downstream gating
            results.append(validate(nr, source.output_schema))
            records.append(nr)

        invalid = sum(1 for r in results if not r.valid)
        status = JobStatus.FAILED if should_fail_job(results) else JobStatus.COMPLETE
        return RunResult(source.id, status, artifact.artifact_id, records, invalid)
    except Exception as e:  # noqa: BLE001 — surface as a failed job, not a crash
        logger.exception("job failed: source=%s", source.id)
        return RunResult(source.id, JobStatus.FAILED, None, [], 0, error=str(e))
