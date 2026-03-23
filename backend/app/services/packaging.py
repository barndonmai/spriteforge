import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.services.storage import get_manifest_path, get_zip_path


def write_manifest(job_id: str, manifest: dict) -> Path:
    manifest_path = get_manifest_path(job_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_manifest_path = manifest_path.with_suffix(".json.tmp")
    temp_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temp_manifest_path.replace(manifest_path)
    return manifest_path


def build_results_zip(job_id: str, final_output_paths: list[Path]) -> Path:
    if not final_output_paths:
        raise ValueError("Cannot package results without any final output assets.")

    zip_path = get_zip_path(job_id)
    manifest_path = get_manifest_path(job_id)
    temp_zip_path = zip_path.with_suffix(".zip.tmp")

    if not manifest_path.exists():
        raise FileNotFoundError("Manifest file is missing and cannot be added to the ZIP package.")

    seen_filenames: set[str] = set()
    for output_path in final_output_paths:
        if not output_path.exists():
            raise FileNotFoundError(f"Missing final output asset: {output_path.name}")
        if output_path.name in seen_filenames:
            raise ValueError(f"Duplicate output filename detected: {output_path.name}")
        seen_filenames.add(output_path.name)

    with ZipFile(temp_zip_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(manifest_path, arcname="manifest.json")

        for output_path in final_output_paths:
            archive.write(output_path, arcname=f"final/{output_path.name}")

    with ZipFile(temp_zip_path, "r") as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"ZIP verification failed for member: {corrupt_member}")

    temp_zip_path.replace(zip_path)
    return zip_path
