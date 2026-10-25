import json
from pathlib import Path

import pyarrow as arrow
import pyarrow.parquet as parquet
import pytest

from ai_dataops.ingestion import ingest_parquet


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    source = tmp_path / "trips.parquet"
    table = arrow.table({"trip_id": [1, 2, 3], "fare_amount": [10.0, 15.5, 8.25]})
    parquet.write_table(table, source)
    return source


def test_ingest_copies_parquet_and_writes_manifest(source_file: Path, tmp_path: Path) -> None:
    bronze_dir = tmp_path / "bronze"

    manifest = ingest_parquet(source_file, bronze_dir, "yellow-2024-01")

    batch_dir = bronze_dir / "yellow-2024-01"
    assert (batch_dir / source_file.name).read_bytes() == source_file.read_bytes()
    stored_manifest = json.loads((batch_dir / "manifest.json").read_text(encoding="utf-8"))
    assert stored_manifest["row_count"] == 3
    assert stored_manifest["batch_id"] == "yellow-2024-01"
    assert stored_manifest["source_sha256"] == manifest.source_sha256
    assert manifest.row_count == 3


def test_reingesting_same_batch_is_idempotent(source_file: Path, tmp_path: Path) -> None:
    bronze_dir = tmp_path / "bronze"

    first = ingest_parquet(source_file, bronze_dir, "batch-001")
    second = ingest_parquet(source_file, bronze_dir, "batch-001")

    assert second == first


def test_reusing_batch_id_for_different_content_fails(source_file: Path, tmp_path: Path) -> None:
    bronze_dir = tmp_path / "bronze"
    ingest_parquet(source_file, bronze_dir, "batch-001")
    changed_source = tmp_path / "changed.parquet"
    parquet.write_table(arrow.table({"trip_id": [4]}), changed_source)

    with pytest.raises(FileExistsError, match="different source file"):
        ingest_parquet(changed_source, bronze_dir, "batch-001")


@pytest.mark.parametrize("batch_id", ["../outside", "bad/id", "", "-starts-with-dash", "x" * 65])
def test_invalid_batch_id_is_rejected(source_file: Path, tmp_path: Path, batch_id: str) -> None:
    with pytest.raises(ValueError, match="batch_id"):
        ingest_parquet(source_file, tmp_path / "bronze", batch_id)
