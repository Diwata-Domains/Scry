"""Fetchers — generic reference acquisition adapters.

`web`, `api`, `file` are fully implemented; `browser` uses Playwright if installed.
Tuned adapters, anti-bot, proxy rotation, and login flows are NOT part of this core.
"""

from __future__ import annotations

import base64
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from scry.models import FetchResult, SourceDefinition
from scry.net import assert_public_url, safe_get

_UA = "scry/0.2.1 (+https://github.com/Diwata-Domains/Scry)"

# request headers redacted before they are persisted into artifact provenance/metadata
_REDACT_HEADERS = {"authorization", "cookie", "proxy-authorization"}


def _redact(headers: dict) -> dict:
    return {k: ("***redacted***" if k.lower() in _REDACT_HEADERS else v) for k, v in headers.items()}


class Fetcher(ABC):
    @abstractmethod
    def fetch(self, source: SourceDefinition) -> FetchResult:
        ...


def _auth_headers(auth: Optional[dict], *, accept: Optional[str] = None) -> dict:
    headers = {"User-Agent": _UA}
    if accept:
        headers["Accept"] = accept
    if not auth:
        return headers
    kind = auth.get("type")
    if kind == "bearer":
        headers["Authorization"] = f"Bearer {auth['token']}"
    elif kind == "api_key":
        headers[auth["header"]] = auth["value"]
    elif kind == "cookie":
        headers["Cookie"] = auth["cookie"]
    elif kind == "basic":
        creds = base64.b64encode(f"{auth['user']}:{auth['password']}".encode()).decode()
        headers["Authorization"] = f"Basic {creds}"
    return headers


def _meta(response, headers: dict, source_type: str) -> dict:
    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "request_headers": _redact(headers),  # never persist auth headers into provenance
        "response_headers": dict(response.headers),
        "duration_ms": int(response.elapsed.total_seconds() * 1000),
        "extraction_context": {"source_type": source_type},
    }


class WebFetcher(Fetcher):
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def fetch(self, source: SourceDefinition) -> FetchResult:
        import httpx

        if source.rate_limit and (delay := source.rate_limit.get("delay_ms", 0) / 1000) > 0:
            time.sleep(delay)
        headers = _auth_headers(source.auth_config)
        with httpx.Client(timeout=self.timeout) as client:
            r = safe_get(client, source.url, headers=headers)  # SSRF-guarded; validates each redirect
            r.raise_for_status()
        ct = r.headers.get("content-type", "text/html").split(";")[0].strip()
        return FetchResult(content=r.content, content_type=ct, metadata=_meta(r, headers, "web"))


class APIFetcher(Fetcher):
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def fetch(self, source: SourceDefinition) -> FetchResult:
        import httpx

        headers = _auth_headers(source.auth_config, accept="application/json")
        with httpx.Client(timeout=self.timeout) as client:
            r = safe_get(client, source.url, headers=headers)  # SSRF-guarded
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 60)))
                r = safe_get(client, source.url, headers=headers)
            r.raise_for_status()
        return FetchResult(content=r.content, content_type="application/json", metadata=_meta(r, headers, "api"))


class FileFetcher(Fetcher):
    """Reads a local file. SECURITY: `source.url` is trusted input — if it can come from an
    externally-managed source registry, construct with `base_dir` to sandbox reads to that
    directory and reject path traversal.
    """

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir).resolve() if base_dir else None

    def fetch(self, source: SourceDefinition) -> FetchResult:
        path = Path(source.url).resolve()
        if self.base_dir and self.base_dir not in path.parents and path != self.base_dir:
            raise ValueError(f"file source escapes base_dir: {path}")
        if not path.exists():
            raise FileNotFoundError(f"file source not found: {path}")
        content = path.read_bytes()
        ct = {".csv": "text/csv", ".json": "application/json",
              ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              ".pdf": "application/pdf"}.get(path.suffix.lower(), "application/octet-stream")
        return FetchResult(content=content, content_type=ct,
                           metadata={"url": str(path.resolve()), "filename": path.name,
                                     "size_bytes": len(content), "extraction_context": {"source_type": "file"}})


class BrowserFetcher(Fetcher):
    """Reference browser fetcher (requires `pip install 'scry-kit[browser]'`)."""

    def fetch(self, source: SourceDefinition) -> FetchResult:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("BrowserFetcher needs: pip install 'scry-kit[browser]' && playwright install chromium") from e
        assert_public_url(source.url)  # SSRF guard before navigating
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(source.url, wait_until="networkidle")
            content, final_url = page.content().encode("utf-8"), page.url
            browser.close()
        return FetchResult(content=content, content_type="text/html",
                           metadata={"url": final_url, "extraction_context": {"source_type": "browser"}})


FETCHERS: dict[str, type[Fetcher]] = {"web": WebFetcher, "api": APIFetcher, "file": FileFetcher, "browser": BrowserFetcher}
