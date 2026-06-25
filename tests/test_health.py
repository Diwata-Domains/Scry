"""Health checks turn a RunResult into a drift verdict; the run log is append-only."""

from scry.health import RunLog, evaluate
from scry.models import JobStatus, NormalizedRecord
from scry.runner import RunResult


def _ok_result():
    recs = [NormalizedRecord("person", {"name": "Ada"}, artifact_id="a1")]
    return RunResult("people", JobStatus.COMPLETE, "a1", recs, invalid=0)


def test_healthy_run_passes():
    r = evaluate(_ok_result(), min_records=1, required_nonempty=["name"])
    assert r.ok and r.reasons == []


def test_zero_records_is_suspect():
    res = RunResult("people", JobStatus.COMPLETE, "a1", [], invalid=0)
    r = evaluate(res, min_records=1)
    assert not r.ok
    assert any("too few records" in reason for reason in r.reasons)


def test_empty_required_field_flags_selector_drift():
    recs = [NormalizedRecord("person", {"name": ""}, artifact_id="a1")]
    res = RunResult("people", JobStatus.COMPLETE, "a1", recs, invalid=0)
    r = evaluate(res, required_nonempty=["name"])
    assert not r.ok
    assert any("name" in reason and "selector" in reason for reason in r.reasons)


def test_failed_job_is_suspect():
    res = RunResult("people", JobStatus.FAILED, None, [], 0, error="login wall")
    r = evaluate(res)
    assert not r.ok
    assert any("job failed" in reason for reason in r.reasons)


def test_run_log_appends_and_reads(tmp_path):
    log = RunLog(tmp_path / "runs.jsonl")
    log.record(evaluate(_ok_result()), artifact_id="a1")
    log.record(evaluate(RunResult("other", JobStatus.COMPLETE, "b1", [], 0)))
    assert len(log.read()) == 2
    assert len(log.read("people")) == 1
    assert log.read("people")[0]["artifact_id"] == "a1"


def test_check_sources_sweep_uses_per_source_health_and_logs(tmp_path):
    from scry.health import check_sources
    from scry.provenance import ArtifactStore
    from scry.sources import source_from_dict

    csv = tmp_path / "people.csv"
    csv.write_text("Name\nAda Lovelace\n")
    good = source_from_dict({
        "name": "people",
        "fetch": {"mode": "file", "url": str(csv)},
        "parse": {"mode": "file", "file_type": "csv", "fields": {"name": "Name"}},
        "output_schema": {"entity_type": "person", "required": ["name"]},
        "health": {"min_records": 1, "required_nonempty": ["name"]},
    })
    drifted = source_from_dict({
        "name": "drifted",
        "fetch": {"mode": "file", "url": str(csv)},
        "parse": {"mode": "file", "file_type": "csv", "fields": {"name": "WrongColumn"}},
        "health": {"required_nonempty": ["name"]},
    })
    assert good.health == {"min_records": 1, "required_nonempty": ["name"]}

    log = RunLog(tmp_path / "runs.jsonl")
    reports = check_sources([good, drifted], ArtifactStore(tmp_path / "store"), run_log=log)
    assert reports[0].ok and not reports[1].ok
    assert len(log.read()) == 2
