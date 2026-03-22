import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.services.storage import get_manifest_path, get_zip_path


def write_manifest(job_id: str, manifest: dict) -> Path:
    manifest_path = get_manifest_path(job_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def build_results_zip(job_id: str, final_output_paths: list[Path]) -> Path:
    zip_path = get_zip_path(job_id)
    manifest_path = get_manifest_path(job_id)

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        if manifest_path.exists():
            archive.write(manifest_path, arcname="manifest.json")

        for output_path in final_output_paths:
            archive.write(output_path, arcname=f"final/{output_path.name}")

    return zip_path

