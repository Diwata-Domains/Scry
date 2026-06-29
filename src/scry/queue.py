"""Generic, dependency-free job queue (file-backed).

A simple append-only queue used by `scry worker`. Jobs are JSON files moved
between pending/processing/done/dead directories; `claim()` uses an atomic
rename so multiple workers don't double-process. This is the generic queue
*abstraction* — a Redis/RQ backend can implement the same interface.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Optional

_SUBDIRS = ("pending", "processing", "done", "dead")


class JobQueue:
    def __init__(self, root: str | Path = "./scry-data"):
        self.q = Path(root) / "queue"
        for sub in _SUBDIRS:
            (self.q / sub).mkdir(parents=True, exist_ok=True)

    def enqueue(self, source_path: str) -> str:
        job_id = uuid.uuid4().hex
        # filename = <ns-timestamp>-<job_id> so sorted() in claim() is FIFO by insertion time;
        # time_ns() is fixed-width (lexicographic == chronological), uuid disambiguates ties.
        (self.q / "pending" / f"{time.time_ns()}-{job_id}.json").write_text(
            json.dumps({"job_id": job_id, "source_path": str(source_path)})
        )
        return job_id

    def claim(self) -> Optional[dict]:
        """Atomically claim the oldest pending job (rename = lock). None if empty."""
        for p in sorted((self.q / "pending").glob("*.json")):
            dest = self.q / "processing" / p.name
            try:
                p.rename(dest)  # atomic on POSIX; loser gets FileNotFoundError
            except FileNotFoundError:
                continue
            return json.loads(dest.read_text())
        return None

    def complete(self, job_id: str) -> None:
        self._move(job_id, "done")

    def fail(self, job_id: str) -> None:
        self._move(job_id, "dead")

    def pending_count(self) -> int:
        return len(list((self.q / "pending").glob("*.json")))

    def _move(self, job_id: str, to: str) -> None:
        for src in (self.q / "processing").glob(f"*{job_id}.json"):  # name carries an ns-prefix
            src.rename(self.q / to / src.name)
