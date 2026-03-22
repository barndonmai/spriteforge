from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app.db.session import SessionLocal, init_db
from app.repositories.jobs import get_job, save_job
from app.services.image_utils import normalize_to_canvas, save_png
from app.services.manifests import build_manifest
from app.services.packaging import build_results_zip, write_manifest
from app.services.providers.base import GeneratedAsset
from app.services.providers.factory import get_image_provider
from app.services.storage import (
    ensure_storage_root,
    get_final_output_directory,
    get_raw_output_directory,
    to_storage_relative_path,
)


def process_job(job_id: str) -> None:
    init_db()
    ensure_storage_root()

    try:
        with SessionLocal() as session:
            job = get_job(session, job_id)
            if not job:
                raise RuntimeError(f"Job {job_id} not found.")

            provider = get_image_provider()
            reference_image_path = ensure_storage_root() / job.reference_image_path

            _update_job(session, job, status="processing", stage="validating_input")
            if not reference_image_path.exists():
                raise FileNotFoundError(f"Reference image is missing for job {job.id}.")

            resolved_mode = job.requested_mode
            if job.requested_mode == "auto":
                _update_job(session, job, status="processing", stage="classifying_mode")
                resolved_mode = provider.classify_reference(reference_image_path, job.notes)

            job.resolved_mode = resolved_mode
            save_job(session, job)

            _update_job(session, job, status="processing", stage="extracting_reference_traits")
            job.reference_summary = provider.summarize_reference(reference_image_path, resolved_mode, job.notes)
            save_job(session, job)

            _update_job(session, job, status="processing", stage="generating_assets")
            raw_output_directory = get_raw_output_directory(job.id)
            generated_assets = _generate_assets(
                provider=provider,
                resolved_mode=resolved_mode,
                reference_image_path=reference_image_path,
                summary=job.reference_summary or {},
                target_size=job.target_size,
                output_dir=raw_output_directory,
            )

            _update_job(session, job, status="processing", stage="normalizing_assets")
            final_assets = _normalize_assets(job.id, generated_assets, job.target_size)

            _update_job(session, job, status="processing", stage="packaging_results")
            job.status = "completed"
            job.stage = None
            job.completed_at = datetime.now(timezone.utc)
            manifest = build_manifest(job, [asset.path for asset in final_assets])
            manifest_path = write_manifest(job.id, manifest)
            zip_path = build_results_zip(job.id, [asset.path for asset in final_assets])

            job.manifest_path = to_storage_relative_path(manifest_path)
            job.zip_path = to_storage_relative_path(zip_path)
            save_job(session, job)

    except Exception as exc:
        with SessionLocal() as session:
            job = get_job(session, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.stage = None
                save_job(session, job)
        raise


def _generate_assets(
    *,
    provider,
    resolved_mode: str,
    reference_image_path: Path,
    summary: dict,
    target_size: int,
    output_dir: Path,
) -> list[GeneratedAsset]:
    if resolved_mode == "character":
        return provider.generate_character_directions(
            reference_image_path=reference_image_path,
            summary=summary,
            target_size=target_size,
            output_dir=output_dir,
        )

    return provider.generate_object_sprite(
        reference_image_path=reference_image_path,
        summary=summary,
        target_size=target_size,
        output_dir=output_dir,
    )


def _normalize_assets(job_id: str, generated_assets: list[GeneratedAsset], target_size: int) -> list[GeneratedAsset]:
    final_output_directory = get_final_output_directory(job_id)
    normalized_assets: list[GeneratedAsset] = []

    for asset in generated_assets:
        image = Image.open(asset.path).convert("RGBA")
        normalized_image = normalize_to_canvas(image, target_size)
        final_path = final_output_directory / asset.filename
        save_png(normalized_image, final_path)
        normalized_assets.append(GeneratedAsset(filename=asset.filename, label=asset.label, path=final_path))

    return normalized_assets


def _update_job(session, job, *, status: str, stage: str | None) -> None:
    job.status = status
    job.stage = stage
    save_job(session, job)
