import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.requests import Request
from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.jobs import create_job, get_job
from app.schemas.jobs import JobResultAsset, JobResultsResponse, JobStatusResponse
from app.services.providers.factory import get_image_provider
from app.services.storage import get_manifest_path, save_reference_upload


def validate_upload(reference_image: UploadFile, mode: str, target_size: int) -> None:
    allowed_modes = {"character", "object", "auto"}
    allowed_content_types = {"image/png", "image/jpeg"}
    allowed_extensions = {".png", ".jpg", ".jpeg"}

    if mode not in allowed_modes:
        raise HTTPException(status_code=422, detail=f"mode must be one of: {', '.join(sorted(allowed_modes))}")

    filename = reference_image.filename or ""
    extension = Path(filename).suffix.lower()
    if reference_image.content_type not in allowed_content_types or extension not in allowed_extensions:
        raise HTTPException(status_code=422, detail="reference_image must be a PNG or JPEG file")

    if target_size <= 0:
        raise HTTPException(status_code=422, detail="target_size must be greater than 0")


def create_job_from_upload(
    session: Session,
    *,
    reference_image: UploadFile,
    mode: str,
    target_size: int,
    notes: str | None,
) -> Job:
    validate_upload(reference_image, mode, target_size)

    job_id = str(uuid4())
    _, reference_image_path = save_reference_upload(job_id, reference_image)
    provider = get_image_provider()

    job = create_job(
        session,
        job_id=job_id,
        requested_mode=mode,
        target_size=target_size,
        notes=notes,
        provider_name=provider.name,
        reference_image_name=reference_image.filename or Path(reference_image_path).name,
        reference_image_path=reference_image_path,
    )
    enqueue_job(job.id)
    return job


def enqueue_job(job_id: str) -> None:
    from app.tasks.jobs import process_job_task

    process_job_task.delay(job_id)


def serialize_job_status(job: Job) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        requested_mode=job.requested_mode,
        resolved_mode=job.resolved_mode,
        target_size=job.target_size,
        error=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def read_results(job: Job, request: Request) -> JobResultsResponse:
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Job results are not ready yet.")
    if not job.manifest_path:
        raise HTTPException(status_code=404, detail="Manifest not found for this job.")

    manifest_path = get_manifest_path(job.id)
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest file is missing on disk.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    outputs = [
        JobResultAsset(
            filename=asset["filename"],
            label=asset["label"],
            storage_path=asset["storage_path"],
            width=job.target_size,
            height=job.target_size,
            url=str(request.url_for("storage", path=asset["storage_path"])),
        )
        for asset in manifest.get("outputs", [])
    ]

    return JobResultsResponse(
        job_id=job.id,
        status=job.status,
        requested_mode=job.requested_mode,
        resolved_mode=job.resolved_mode or job.requested_mode,
        target_size=job.target_size,
        provider=job.provider_name,
        reference_image_path=job.reference_image_path,
        reference_summary=job.reference_summary,
        manifest_path=job.manifest_path,
        download_url=str(request.url_for("download_job_results", job_id=job.id)),
        outputs=outputs,
    )


def get_job_or_404(session: Session, job_id: str) -> Job:
    job = get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
