"""Provenance — the standout layer.

Every fetch is recorded as an immutable **Artifact**: a timestamped, checksummed
record of exactly what was seen, plus the raw bytes stored content-addressed
(deduplicated by SHA-256). Artifacts are append-only; blobs are never overwritten.

  - `replay(artifact_id)` returns the exact bytes that were fetched.
  - `diff(a, b)` shows what changed between two captures.

Store layout (local filesystem, self-hosted):
    <store>/artifacts/<artifact_id>.json   # manifest (append-only)
    <store>/blobs/<sha256>.bin             # raw content (content-addressed, dedup)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any, Optional

from scry.models import FetchResult


@dataclass
class Artifact:
    """An immutable, timestamped record of one fetch."""

    artifact_id: str
    source_id: str
    captured_at: str  # ISO-8601 UTC
    content_type: str
    content_sha256: str
    size: int
    metadata: dict[str, Any] = field(default_factory=dict)


def _utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class ArtifactStore:
    """Self-hosted, append-only provenance store on the local filesystem."""

    def __init__(self, root: str | Path = "./scry-data"):
        self.root = Path(root)
        self.artifacts_dir = self.root / "artifacts"
        self.blobs_dir = self.root / "blobs"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.blobs_dir.mkdir(parents=True, exist_ok=True)

    def write(self, source_id: str, result: FetchResult, captured_at: Optional[str] = None) -> Artifact:
        """Record a fetch as an immutable artifact. Blob is deduplicated by checksum."""
        sha = hashlib.sha256(result.content).hexdigest()
        blob = self.blobs_dir / f"{sha}.bin"
        if not blob.exists():  # content-addressed: never overwrite
            blob.write_bytes(result.content)
        art = Artifact(
            artifact_id=uuid.uuid4().hex,
            source_id=source_id,
            captured_at=captured_at or _utcnow_iso(),
            content_type=result.content_type,
            content_sha256=sha,
            size=len(result.content),
            metadata=result.metadata,
        )
        (self.artifacts_dir / f"{art.artifact_id}.json").write_text(
            json.dumps(asdict(art), indent=2, sort_keys=True)
        )
        return art

    def get(self, artifact_id: str) -> Artifact:
        path = self.artifacts_dir / f"{artifact_id}.json"
        if not path.exists():
            raise KeyError(f"artifact not found: {artifact_id}")
        return Artifact(**json.loads(path.read_text()))

    def replay(self, artifact_id: str) -> bytes:
        """Return the exact bytes that were fetched for this artifact."""
        art = self.get(artifact_id)
        blob = self.blobs_dir / f"{art.content_sha256}.bin"
        if not blob.exists():
            raise FileNotFoundError(f"blob missing for artifact {artifact_id}: {art.content_sha256}")
        return blob.read_bytes()

    def list(self, source_id: Optional[str] = None) -> list[Artifact]:
        arts = [Artifact(**json.loads(p.read_text())) for p in self.artifacts_dir.glob("*.json")]
        if source_id is not None:
            arts = [a for a in arts if a.source_id == source_id]
        return sorted(arts, key=lambda a: a.captured_at)

    def diff(self, artifact_a: str, artifact_b: str) -> str:
        """Unified text diff between two artifacts' contents (best-effort decode)."""
        a, b = self.get(artifact_a), self.get(artifact_b)
        if a.content_sha256 == b.content_sha256:
            return ""
        ta = self.replay(artifact_a).decode("utf-8", errors="replace").splitlines()
        tb = self.replay(artifact_b).decode("utf-8", errors="replace").splitlines()
        return "\n".join(unified_diff(ta, tb, fromfile=f"{artifact_a} @ {a.captured_at}",
                                      tofile=f"{artifact_b} @ {b.captured_at}", lineterm=""))
