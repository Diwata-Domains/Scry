"""Parsers — deterministic, rule-based extraction.

`html` uses CSS selectors with a `::text` / `::attr(name)` suffix; `json_path` uses
dot-notation; `file` handles CSV/JSON (XLSX/PDF via the `files` extra). When a
`records` selector is given, one record is emitted per match. No ML, no black boxes.
"""

from __future__ import annotations

import csv
import io
import json
import re
from abc import ABC, abstractmethod
from typing import Any

from scry.models import ParsedRecord

_FIELD_RE = re.compile(r"^(?P<sel>.*?)::(?P<kind>text|attr\((?P<attr>[^)]+)\))$")


def _parse_field_spec(spec: str) -> tuple[str, str]:
    """'h2.title::text' -> ('h2.title', 'text'); 'a::attr(href)' -> ('a', 'href')."""
    m = _FIELD_RE.match(spec.strip())
    if not m:
        return spec.strip(), "text"  # bare selector defaults to text
    if m.group("attr") is not None:
        return m.group("sel"), m.group("attr")
    return m.group("sel"), "text"


class Parser(ABC):
    @abstractmethod
    def parse(self, content: bytes, extraction_rules: dict) -> list[ParsedRecord]:
        ...


class HTMLParser(Parser):
    def parse(self, content: bytes, rules: dict) -> list[ParsedRecord]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")
        fields = rules.get("fields", {})
        records_sel = rules.get("records")
        scopes = soup.select(records_sel) if records_sel else [soup]
        return [self._extract(scope, fields) for scope in scopes]

    @staticmethod
    def _extract(scope, fields: dict) -> ParsedRecord:
        out: dict[str, Any] = {}
        for name, spec in fields.items():
            selector, attr = _parse_field_spec(spec)
            el = scope.select_one(selector) if selector else scope
            if el is None:
                out[name] = None
            elif attr == "text":
                out[name] = el.get_text(strip=True)
            else:
                out[name] = el.get(attr)
        return ParsedRecord(fields=out)


def _nested(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)] if int(part) < len(cur) else None
        else:
            return None
        if cur is None:
            return None
    return cur


class JSONParser(Parser):
    def parse(self, content: bytes, rules: dict) -> list[ParsedRecord]:
        data = json.loads(content)
        records = rules.get("records")
        fields = rules.get("fields", {})
        if records:
            items = _nested(data, records)
            items = items if isinstance(items, list) else ([items] if items is not None else [])
        else:
            items = data if isinstance(data, list) else [data]
        return [ParsedRecord(fields={n: _nested(it, p) for n, p in fields.items()}) for it in items]


class FileParser(Parser):
    def parse(self, content: bytes, rules: dict) -> list[ParsedRecord]:
        ft = rules.get("file_type", "csv")
        fields = rules.get("fields", {})
        if ft == "csv":
            reader = csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace")))
            return [ParsedRecord(fields={k: row.get(v) for k, v in fields.items()}) for row in reader]
        if ft == "json":
            data = json.loads(content)
            rows = data if isinstance(data, list) else [data]
            return [ParsedRecord(fields={k: row.get(v) for k, v in fields.items()}) for row in rows]
        if ft == "xlsx":
            return self._xlsx(content, fields)
        if ft == "pdf":
            return self._pdf(content)
        raise ValueError(f"unsupported file_type: {ft!r}")

    @staticmethod
    def _xlsx(content: bytes, fields: dict) -> list[ParsedRecord]:
        try:
            import openpyxl
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("XLSX needs the extra: pip install 'scry[files]'") from e
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        rows = list(wb.active.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h) if h is not None else "" for h in rows[0]]
        return [ParsedRecord(fields={k: dict(zip(headers, r)).get(v) for k, v in fields.items()}) for r in rows[1:]]

    @staticmethod
    def _pdf(content: bytes) -> list[ParsedRecord]:
        try:
            import pdfplumber
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("PDF needs the extra: pip install 'scry[files]'") from e
        parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                if t := page.extract_text():
                    parts.append(t)
        return [ParsedRecord(fields={"content": "\n".join(parts)})]


PARSERS: dict[str, type[Parser]] = {"html": HTMLParser, "json_path": JSONParser, "file": FileParser}
