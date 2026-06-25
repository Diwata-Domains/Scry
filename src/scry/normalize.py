"""Normalizer — generic type coercion, date parsing, URL/string normalization.

Applied after parsing, before validation. Deterministic and rule-based.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse

from scry.models import NormalizedRecord, ParsedRecord

_DATE_FORMATS = ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]


def _parse_date(value: str) -> str:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return value


def _normalize_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")
    return urlunparse(parsed)


def _normalize_value(key: str, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        lower = key.lower()
        if "url" in lower:
            return _normalize_url(value)
        if "date" in lower or lower.endswith("_at") or lower == "published":
            return _parse_date(value)
    return value


def normalize(record: ParsedRecord, entity_type: str) -> NormalizedRecord:
    data = {k: _normalize_value(k, v) for k, v in record.fields.items()}
    if not any(v is not None for v in data.values()):
        return NormalizedRecord(entity_type=entity_type, data={})
    return NormalizedRecord(entity_type=entity_type, data=data)
