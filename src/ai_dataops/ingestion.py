"""Local, idempotent ingestion of Parquet source files into the Bronze layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as parquet

logger = logging.getLogger(__name__)
_BATCH_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


@dataclass(frozen=True)
class IngestionManifest:
    batch_id: str
    source_filename: str
    source_sha256: str
    row_count: int
    ingestion_timestamp: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _existing_manifest(batch_dir: Path, batch_id: str, source: Path, source_sha256: str) -> IngestionManifest:
    manifest_path = batch_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileExistsError(f"Bronze batch directory already exists without a manifest: {batch_dir}")

    with manifest_path.open(encoding="utf-8") as manifest_file:
        manifest = IngestionManifest(**json.load(manifest_file))

    if manifest.batch_id != batch_id:
        raise ValueError(f"Manifest batch ID does not match directory name: {batch_dir}")
    if manifest.source_filename != source.name or manifest.source_sha256 != source_sha256:
        raise FileExistsError(f"Batch ID '{batch_id}' was already used for a different source file")
    return manifest


def ingest_parquet(source_path: Path, bronze_dir: Path, batch_id: str) -> IngestionManifest:
    """Copy one Parquet file and its manifest into a batch-specific Bronze directory.

    Reusing a batch ID for the same named file and content is a no-op. Reusing it
    for different content is rejected to prevent accidental data replacement.
    """
    if not _BATCH_ID_PATTERN.fullmatch(batch_id):
        raise ValueError("batch_id must start with a letter or digit and contain at most 64 letters, digits, '_' or '-'")

    source = source_path.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    if source.suffix.lower() != ".parquet":
        raise ValueError(f"Only Parquet source files are supported: {source}")

    source_sha256 = _sha256_file(source)
    batch_dir = bronze_dir / batch_id
    if batch_dir.exists():
        manifest = _existing_manifest(batch_dir, batch_id, source, source_sha256)
        logger.info("Ingestion batch already exists", extra={"batch_id": batch_id, "source": str(source)})
        return manifest

    row_count = parquet.ParquetFile(source).metadata.num_rows
    manifest = IngestionManifest(
        batch_id=batch_id,
        source_filename=source.name,
        source_sha256=source_sha256,
        row_count=row_count,
        ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    bronze_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{batch_id}-", dir=bronze_dir) as temporary_dir:
        staged_batch = Path(temporary_dir) / "batch"
        staged_batch.mkdir()
        shutil.copy2(source, staged_batch / source.name)
        with (staged_batch / "manifest.json").open("w", encoding="utf-8") as manifest_file:
            json.dump(asdict(manifest), manifest_file, indent=2)
            manifest_file.write("\n")
        os.replace(staged_batch, batch_dir)

    logger.info(
        "Ingested Parquet source",
        extra={"batch_id": batch_id, "source": str(source), "row_count": row_count},
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy a Parquet file into the local Bronze layer.")
    parser.add_argument("--source", required=True, type=Path, help="Path to the source Parquet file")
    parser.add_argument("--batch-id", required=True, help="Stable ID for this ingestion batch")
    parser.add_argument("--bronze-dir", type=Path, default=Path("data/bronze"), help="Bronze output directory")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    manifest = ingest_parquet(args.source, args.bronze_dir, args.batch_id)
    print(json.dumps(asdict(manifest), indent=2))


if __name__ == "__main__":
    main()
