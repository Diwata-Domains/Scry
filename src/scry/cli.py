"""scry — command-line interface.

    scry run <source.yaml>          acquire + capture, print records + artifact id
    scry artifacts list             list captures
    scry replay <artifact-id>       print the exact bytes that were fetched
    scry replay --diff <a> <b>      unified diff between two captures
    scry worker                     process queued jobs
    scry scheduler                  enqueue sources whose cron is due
    scry mcp                        run the MCP stdio server
"""

from __future__ import annotations

import json
import sys
import time

import click

from scry.provenance import ArtifactStore
from scry.queue import JobQueue
from scry.runner import run_source as _run_source
from scry.sources import load_source

_store_opt = click.option("--store", "store_dir", default="./scry-data", show_default=True, help="Provenance store directory.")
_sources_opt = click.option("--sources", "sources_dir", default="./sources", show_default=True, help="Directory of source-definition YAML files.")


@click.group()
@click.version_option(package_name="scry-kit")
def main() -> None:
    """Scry — provenance-first acquisition."""


@main.command()
@click.argument("source_path", type=click.Path(exists=True, dir_okay=False))
@_store_opt
def run(source_path: str, store_dir: str) -> None:
    """Run the pipeline for SOURCE_PATH (a source-definition YAML)."""
    result = _run_source(load_source(source_path), ArtifactStore(store_dir))
    click.echo(json.dumps(result.to_dict(), indent=2, default=str))
    if result.status.value == "failed":
        sys.exit(1)


@main.group()
def artifacts() -> None:
    """Inspect provenance artifacts."""


@artifacts.command(name="list")
@_store_opt
@click.option("--source", "source_id", default=None, help="Filter by source id.")
def artifacts_list(store_dir: str, source_id: str | None) -> None:
    """List captured artifacts."""
    for a in ArtifactStore(store_dir).list(source_id):
        click.echo(f"{a.captured_at}  {a.artifact_id}  {a.source_id}  {a.content_sha256[:12]}  {a.size}B")


@main.command()
@click.argument("artifact_ids", nargs=-1, required=True)
@_store_opt
@click.option("--diff", "do_diff", is_flag=True, help="Diff two artifacts instead of replaying one.")
@click.option("--out", type=click.Path(dir_okay=False), help="Write replayed bytes to a file.")
def replay(artifact_ids: tuple[str, ...], store_dir: str, do_diff: bool, out: str | None) -> None:
    """Replay an artifact's exact bytes, or --diff two artifacts."""
    store = ArtifactStore(store_dir)
    if do_diff:
        if len(artifact_ids) != 2:
            raise click.UsageError("--diff needs exactly two artifact ids")
        d = store.diff(*artifact_ids)
        click.echo(d if d else "(identical content)")
        return
    if len(artifact_ids) != 1:
        raise click.UsageError("replay needs exactly one artifact id (or use --diff with two)")
    content = store.replay(artifact_ids[0])
    if out:
        with open(out, "wb") as fh:
            fh.write(content)
        click.echo(f"wrote {len(content)} bytes to {out}")
    else:
        click.echo(content.decode("utf-8", errors="replace"))


@main.command()
@_store_opt
@_sources_opt
@click.option("--once", is_flag=True, help="Drain the queue once and exit (otherwise loop).")
def worker(store_dir: str, sources_dir: str, once: bool) -> None:
    """Process queued jobs: claim -> run -> mark done/dead."""
    store, q = ArtifactStore(store_dir), JobQueue(store_dir)
    while True:
        job = q.claim()
        if job is None:
            if once:
                break
            time.sleep(2)
            continue
        try:
            result = _run_source(load_source(job["source_path"]), store)
            (q.complete if result.status.value != "failed" else q.fail)(job["job_id"])
            click.echo(f"{job['job_id']}  {job['source_path']}  -> {result.status.value} ({len(result.records)} records)")
        except Exception as e:  # noqa: BLE001
            q.fail(job["job_id"])
            click.echo(f"{job['job_id']}  {job['source_path']}  -> error: {e}", err=True)


@main.command()
@_store_opt
@_sources_opt
@click.option("--once", is_flag=True, help="Run one scheduling pass and exit.")
def scheduler(store_dir: str, sources_dir: str, once: bool) -> None:
    """Enqueue sources whose cron schedule is due (run with `scry worker`)."""
    from datetime import datetime, timezone

    from scry.scheduler import run_due

    q = JobQueue(store_dir)
    while True:
        now = datetime.now(tz=timezone.utc)
        enq = run_due(sources_dir, q, now)
        if enq:
            click.echo(f"{now.isoformat()}  enqueued {len(enq)}: {', '.join(enq)}")
        if once:
            break
        time.sleep(60)


@main.command()
@_store_opt
def mcp(store_dir: str) -> None:
    """Run the MCP stdio server (generic acquisition tools)."""
    from scry.mcp import serve_stdio

    serve_stdio(ArtifactStore(store_dir))


if __name__ == "__main__":  # pragma: no cover
    main()
