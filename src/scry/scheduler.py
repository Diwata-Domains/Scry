"""Scheduler — enqueue sources whose cron schedule is due.

Dependency-free 5-field cron matcher (minute hour day-of-month month day-of-week),
supporting `*`, numbers, lists `a,b`, ranges `a-b`, and steps `*/n`. `scry scheduler`
loops once per minute and enqueues due sources for `scry worker` to run.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scry.queue import JobQueue
from scry.sources import source_from_dict


def _match_field(expr: str, value: int, lo: int, hi: int) -> bool:
    for part in expr.split(","):
        part = part.strip()
        if part == "*":
            return True
        if part.startswith("*/"):
            step = int(part[2:])
            if step > 0 and (value - lo) % step == 0:
                return True
        elif "-" in part:
            a, b = part.split("-", 1)
            if int(a) <= value <= int(b):
                return True
        elif part.isdigit() and int(part) == value:
            return True
    return False


def cron_matches(expr: str, dt: datetime) -> bool:
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"cron needs 5 fields, got {len(fields)}: {expr!r}")
    minute, hour, dom, month, dow = fields
    cron_dow = (dt.weekday() + 1) % 7  # Python Mon=0..Sun=6 -> cron Sun=0..Sat=6
    return (
        _match_field(minute, dt.minute, 0, 59)
        and _match_field(hour, dt.hour, 0, 23)
        and _match_field(dom, dt.day, 1, 31)
        and _match_field(month, dt.month, 1, 12)
        and _match_field(dow, cron_dow, 0, 6)
    )


def run_due(sources_dir: str | Path, queue: JobQueue, now: datetime) -> list[str]:
    """Enqueue every enabled source in `sources_dir` whose cron matches `now`. Returns paths."""
    import yaml

    enqueued: list[str] = []
    d = Path(sources_dir)
    for path in sorted([*d.glob("*.yaml"), *d.glob("*.yml")]):
        data = yaml.safe_load(path.read_text()) or {}
        src = source_from_dict(data, source_id=path.stem)
        if src.enabled and src.schedule and src.schedule != "on_demand" and cron_matches(src.schedule, now):
            queue.enqueue(str(path))
            enqueued.append(str(path))
    return enqueued
