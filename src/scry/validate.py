"""Validator — checks normalized records against the source's output_schema.

Failed records are flagged with reasons (dead-letter), never silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from scry.models import NormalizedRecord


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


def validate(record: NormalizedRecord, output_schema: Optional[dict]) -> ValidationResult:
    if not output_schema:
        return ValidationResult(valid=True, errors=[])
    errors: list[str] = []
    for f in output_schema.get("required", []):
        if record.data.get(f) is None:
            errors.append(f"required field missing: {f}")
    for f, expected in output_schema.get("types", {}).items():
        value = record.data.get(f)
        if value is None:
            continue
        if expected == "string" and not isinstance(value, str):
            errors.append(f"field {f}: expected string, got {type(value).__name__}")
        elif expected == "number" and not isinstance(value, (int, float)):
            errors.append(f"field {f}: expected number, got {type(value).__name__}")
    return ValidationResult(valid=not errors, errors=errors)


def should_fail_job(results: list[ValidationResult], threshold: float = 0.5) -> bool:
    if not results:
        return False
    invalid = sum(1 for r in results if not r.valid)
    return (invalid / len(results)) > threshold
