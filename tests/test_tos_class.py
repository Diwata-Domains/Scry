"""tos_class travels source -> artifact -> record, so consumers can gate captures."""

import pytest

from scry.models import ToSClass
from scry.provenance import ArtifactStore
from scry.runner import run_source
from scry.sources import source_from_dict


def _file_source_dict(csv_path, **extra):
    return {
        "name": "people",
        "fetch": {"mode": "file", "url": str(csv_path)},
        "parse": {"mode": "file", "file_type": "csv", "fields": {"name": "Name"}},
        "output_schema": {"entity_type": "person", "required": ["name"]},
        **extra,
    }


def _write_csv(tmp_path):
    p = tmp_path / "people.csv"
    p.write_text("Name\nAda Lovelace\n")
    return p


def test_default_tos_class_is_clean_public(tmp_path):
    src = source_from_dict(_file_source_dict(_write_csv(tmp_path)))
    assert src.tos_class is ToSClass.CLEAN_PUBLIC
    result = run_source(src, ArtifactStore(tmp_path / "store"))
    assert result.records[0].tos_class == "clean_public"


def test_tos_class_travels_source_to_artifact_to_record(tmp_path):
    src = source_from_dict(_file_source_dict(_write_csv(tmp_path), tos_class="restricted_internal"))
    assert src.tos_class is ToSClass.RESTRICTED_INTERNAL
    store = ArtifactStore(tmp_path / "store")
    result = run_source(src, store)
    assert result.records[0].tos_class == "restricted_internal"
    # persisted on the artifact and survives reload
    art = store.get(result.artifact_id)
    assert art.tos_class == "restricted_internal"


def test_invalid_tos_class_rejected(tmp_path):
    with pytest.raises(ValueError):
        source_from_dict(_file_source_dict(_write_csv(tmp_path), tos_class="bogus"))
