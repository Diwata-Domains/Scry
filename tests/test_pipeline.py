from scry.models import JobStatus, SourceDefinition
from scry.provenance import ArtifactStore
from scry.runner import run_source
from scry.sources import source_from_dict


def test_file_source_end_to_end(tmp_path):
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("Name,Email\nAda Lovelace,ada@example.com\nAlan Turing,alan@example.com\n")
    source = SourceDefinition(
        id="people", name="people", source_type="file", parser="file", url=str(csv_path),
        extraction_rules={"file_type": "csv", "fields": {"name": "Name", "email": "Email"}},
        output_schema={"entity_type": "person", "required": ["name"]},
    )
    result = run_source(source, ArtifactStore(tmp_path / "store"))
    assert result.status is JobStatus.COMPLETE
    assert result.artifact_id is not None
    assert len(result.records) == 2
    assert result.records[0].data["name"] == "Ada Lovelace"
    assert result.records[0].artifact_id == result.artifact_id
    assert result.invalid == 0


def test_source_from_dict_yaml_shape():
    src = source_from_dict({
        "name": "articles",
        "fetch": {"mode": "web", "url": "https://example.com"},
        "parse": {"mode": "html", "records": "article.post", "fields": {"title": "h2::text"}},
        "output_schema": {"entity_type": "article"},
        "schedule": "0 * * * *",
    })
    assert src.id == "articles"
    assert src.source_type == "web"
    assert src.parser == "html"
    assert src.extraction_rules["records"] == "article.post"
    assert src.schedule == "0 * * * *"
