from scry.queue import JobQueue


def test_enqueue_claim_complete(tmp_path):
    q = JobQueue(tmp_path)
    q.enqueue("sources/a.yaml")
    q.enqueue("sources/b.yaml")
    assert q.pending_count() == 2

    job = q.claim()
    assert job is not None and job["source_path"] == "sources/a.yaml"
    assert q.pending_count() == 1
    q.complete(job["job_id"])
    assert (tmp_path / "queue" / "done" / f"{job['job_id']}.json").exists()


def test_claim_empty(tmp_path):
    assert JobQueue(tmp_path).claim() is None
