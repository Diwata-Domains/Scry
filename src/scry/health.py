"""Health checks + a run log for acquisition.

Scrapers and crawlers break *silently* when a site changes underneath them — a
selector moves, a login wall appears, a page returns zero rows. Unit tests can't catch
that (the world changed, not your code). This module turns each ``RunResult`` into a
pass/suspect verdict with reasons, and appends an audit line to an append-only JSONL
run log you can watch for drift over time.

    from scry import run_source, evaluate, RunLog
    result = run_source(source, store)
    report = evaluate(result, min_records=1, required_nonempty=["title"])
    RunLog().record(report)
    if not report.ok:
        ...  # alert / trigger re-auth / open a task
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from scry.runner import RunResult


@dataclass
class HealthReport:
    """A pass/suspect verdict for one run, with human-readable reasons."""

    source_id: str
    ok: bool
    status: str
    records: int
    invalid: int
    reasons: list[str] = field(default_factory=list)


def evaluate(
    result: RunResult,
    *,
    min_records: int = 1,
    required_nonempty: Iterable[str] = (),
) -> HealthReport:
    """Judge a run. Empty `required_nonempty` fields or too-few records usually mean
    the site changed (selector drift) or a login wall appeared — not a code bug.
    """
    reasons: list[str] = []
    if result.status.value == "failed":
        reasons.append(f"job failed: {result.error or 'unknown error'}")
    n = len(result.records)
    if n < min_records:
        reasons.append(f"too few records: {n} < {min_records} (selector drift or login wall?)")
    if result.invalid:
        reasons.append(f"{result.invalid} record(s) failed validation")
    for name in required_nonempty:
        if not any(r.data.get(name) for r in result.records):
            reasons.append(f"required field empty in every record: {name!r} (selector likely broke)")
    return HealthReport(result.source_id, not reasons, result.status.value, n, result.invalid, reasons)


class RunLog:
    """Append-only JSONL log of acquisition runs — audit trail + drift watch."""

    def __init__(self, path: str | Path = "./scry-data/runs.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, report: HealthReport, *, at: Optional[str] = None, **extra) -> dict:
        """Append one run's health report (plus any extra fields, e.g. artifact_id)."""
        row = {"at": at or datetime.now(tz=timezone.utc).isoformat(), **asdict(report), **extra}
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        return row

    def read(self, source_id: Optional[str] = None) -> list[dict]:
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]
        return [r for r in rows if source_id is None or r.get("source_id") == source_id]
