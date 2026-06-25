"""Generic MCP surface for Scry.

`TOOLS` are the tool *definitions* (the public agent-facing surface). `serve_stdio()`
is a minimal, dependency-free JSON-RPC-over-stdio server implementing the core MCP
methods (`initialize`, `tools/list`, `tools/call`) for those tools — a reference
implementation. Binding Scry into a specific agent runtime (permissions, dispatch,
product wiring) is intentionally out of scope for this core.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from scry.provenance import ArtifactStore
from scry.runner import run_source
from scry.sources import load_source

PROTOCOL_VERSION = "2024-11-05"

TOOLS: list[dict] = [
    {
        "name": "scry_run",
        "description": "Run the acquisition pipeline for a source-definition YAML file; returns records + the provenance artifact id.",
        "inputSchema": {"type": "object", "properties": {"source_path": {"type": "string"}}, "required": ["source_path"]},
    },
    {
        "name": "scry_replay",
        "description": "Return the exact raw bytes that were fetched for an artifact id (reproducibility).",
        "inputSchema": {"type": "object", "properties": {"artifact_id": {"type": "string"}}, "required": ["artifact_id"]},
    },
    {
        "name": "scry_list_artifacts",
        "description": "List provenance artifacts, optionally filtered by source id.",
        "inputSchema": {"type": "object", "properties": {"source_id": {"type": "string"}}, "required": []},
    },
]


def _call_tool(name: str, args: dict, store: ArtifactStore) -> str:
    if name == "scry_run":
        return json.dumps(run_source(load_source(args["source_path"]), store).to_dict(), default=str)
    if name == "scry_replay":
        return store.replay(args["artifact_id"]).decode("utf-8", errors="replace")
    if name == "scry_list_artifacts":
        return json.dumps([
            {"artifact_id": a.artifact_id, "source_id": a.source_id, "captured_at": a.captured_at,
             "sha256": a.content_sha256, "size": a.size}
            for a in store.list(args.get("source_id"))
        ])
    raise ValueError(f"unknown tool: {name}")


def _handle(req: dict, store: ArtifactStore) -> dict | None:
    method, rid = req.get("method"), req.get("id")
    if method == "initialize":
        result: Any = {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
                       "serverInfo": {"name": "scry", "version": "0.2.0"}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = req.get("params", {})
        try:
            text = _call_tool(params["name"], params.get("arguments", {}), store)
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:  # noqa: BLE001
            result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
    elif method is not None and method.startswith("notifications/"):
        return None  # notifications get no response
    else:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def serve_stdio(store: ArtifactStore) -> None:
    """Minimal MCP stdio server: one JSON-RPC message per line on stdin/stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(req, store)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
