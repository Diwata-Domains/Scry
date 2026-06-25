from scry.models import FetchResult
from scry.provenance import ArtifactStore


def _fr(body: bytes) -> FetchResult:
    return FetchResult(content=body, content_type="text/plain", metadata={"url": "x"})


def test_capture_replay_roundtrip(tmp_path):
    store = ArtifactStore(tmp_path)
    a = store.write("src", _fr(b"hello world"))
    assert store.replay(a.artifact_id) == b"hello world"
    assert store.get(a.artifact_id).source_id == "src"


def test_blob_dedup_same_content(tmp_path):
    store = ArtifactStore(tmp_path)
    a = store.write("src", _fr(b"same"))
    b = store.write("src", _fr(b"same"))
    assert a.artifact_id != b.artifact_id          # captures are append-only
    assert a.content_sha256 == b.content_sha256     # content deduplicated
    assert len(list((tmp_path / "blobs").glob("*.bin"))) == 1


def test_diff(tmp_path):
    store = ArtifactStore(tmp_path)
    a = store.write("src", _fr(b"line1\nline2\n"))
    b = store.write("src", _fr(b"line1\nCHANGED\n"))
    assert "CHANGED" in store.diff(a.artifact_id, b.artifact_id)
    assert store.diff(a.artifact_id, a.artifact_id) == ""


def test_list_filter(tmp_path):
    store = ArtifactStore(tmp_path)
    store.write("a", _fr(b"1"))
    store.write("b", _fr(b"2"))
    assert len(store.list()) == 2
    assert len(store.list("a")) == 1
